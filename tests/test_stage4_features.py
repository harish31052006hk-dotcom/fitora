from decimal import Decimal
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from food_diary.models import FoodEntry
from progress.models import WeightLog

class Stage4ProgressAndAnalyticsTests(TestCase):
    def setUp(self):
        self.client_a = Client()
        self.user_a = User.objects.create_user('dan', 'dan@fitora.local', 'Password123!')
        self.profile_a = Profile.objects.get_or_create(user=self.user_a)[0]
        self.profile_a.daily_calorie_goal = Decimal('2000.00')
        self.profile_a.target_weight = Decimal('70.00')
        self.profile_a.save()

        self.client_b = Client()
        self.user_b = User.objects.create_user('eve', 'eve@fitora.local', 'Password123!')

        self.today = timezone.now().date()

    def test_weight_recording_and_profile_update(self):
        """User can log weight measurement and profile current_weight updates automatically"""
        self.client_a.login(username='dan', password='Password123!')

        resp = self.client_a.post(reverse('progress'), {
            'date': self.today.isoformat(),
            'weight': '75.5',
            'notes': 'Morning fasted'
        })
        self.assertEqual(resp.status_code, 302)

        log = WeightLog.objects.filter(user=self.user_a, date=self.today).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.weight, Decimal('75.50'))
        self.assertEqual(log.notes, 'Morning fasted')

        self.profile_a.refresh_from_db()
        self.assertEqual(self.profile_a.current_weight, Decimal('75.50'))

    def test_weight_edit_and_delete(self):
        """User can edit and delete their own weight log record"""
        self.client_a.login(username='dan', password='Password123!')

        log = WeightLog.objects.create(
            user=self.user_a,
            date=self.today - timedelta(days=2),
            weight=Decimal('76.00'),
            notes='Old measurement'
        )

        # 1. Edit record
        edit_resp = self.client_a.post(reverse('edit_weight', args=[log.id]), {
            'date': (self.today - timedelta(days=2)).isoformat(),
            'weight': '75.8',
            'notes': 'Corrected measurement'
        })
        self.assertEqual(edit_resp.status_code, 302)
        log.refresh_from_db()
        self.assertEqual(log.weight, Decimal('75.80'))
        self.assertEqual(log.notes, 'Corrected measurement')

        # 2. Delete record
        del_resp = self.client_a.post(reverse('delete_weight', args=[log.id]))
        self.assertEqual(del_resp.status_code, 302)
        self.assertFalse(WeightLog.objects.filter(id=log.id).exists())

    def test_weight_ownership_isolation(self):
        """User Eve cannot view, edit, or delete User Dan's weight records"""
        log_dan = WeightLog.objects.create(
            user=self.user_a,
            date=self.today,
            weight=Decimal('75.00')
        )

        self.client_b.login(username='eve', password='Password123!')

        # Attempt to edit Dan's weight log -> 404
        edit_attempt = self.client_b.post(reverse('edit_weight', args=[log_dan.id]), {
            'date': self.today.isoformat(),
            'weight': '80.0'
        })
        self.assertEqual(edit_attempt.status_code, 404)

        # Attempt to delete Dan's weight log -> 404
        del_attempt = self.client_b.post(reverse('delete_weight', args=[log_dan.id]))
        self.assertEqual(del_attempt.status_code, 404)
        self.assertTrue(WeightLog.objects.filter(id=log_dan.id).exists())

    def test_server_side_validation_weight_and_date(self):
        """Server rejects negative/extreme weights and future dates"""
        self.client_a.login(username='dan', password='Password123!')

        # Invalid weight: 5 kg (below minimum 20 kg)
        resp_low = self.client_a.post(reverse('progress'), {
            'date': self.today.isoformat(),
            'weight': '5.0'
        })
        self.assertEqual(resp_low.status_code, 200)
        self.assertFormError(resp_low.context['form'], 'weight', 'Please enter a valid weight between 20.0 kg and 500.0 kg.')

        # Invalid date: Future date
        future_date = self.today + timedelta(days=5)
        resp_future = self.client_a.post(reverse('progress'), {
            'date': future_date.isoformat(),
            'weight': '75.0'
        })
        self.assertEqual(resp_future.status_code, 200)
        self.assertFormError(resp_future.context['form'], 'date', 'Measurement date cannot be in the future.')

    def test_nutrition_aggregation_and_summary_metrics(self):
        """Calculates daily calories, averages, and days tracked from actual diary entries"""
        self.client_a.login(username='dan', password='Password123!')

        # Log Day 1: 1800 kcal, 100g P, 200g C, 50g F
        FoodEntry.objects.create(
            user=self.user_a,
            date=self.today - timedelta(days=1),
            meal_category='Breakfast',
            food_name='Healthy Oatmeal',
            quantity=Decimal('1.00'),
            calories=Decimal('1800.00'),
            protein=Decimal('100.00'),
            carbohydrates=Decimal('200.00'),
            fat=Decimal('50.00')
        )

        # Log Day 2 (Today): 2200 kcal, 120g P, 220g C, 60g F
        FoodEntry.objects.create(
            user=self.user_a,
            date=self.today,
            meal_category='Lunch',
            food_name='Salmon Bowl',
            quantity=Decimal('1.00'),
            calories=Decimal('2200.00'),
            protein=Decimal('120.00'),
            carbohydrates=Decimal('220.00'),
            fat=Decimal('60.00')
        )

        # Log 2 weights to verify weight change
        WeightLog.objects.create(user=self.user_a, date=self.today - timedelta(days=10), weight=Decimal('78.00'))
        WeightLog.objects.create(user=self.user_a, date=self.today, weight=Decimal('76.50'))

        resp = self.client_a.get(reverse('progress') + '?range=7')
        self.assertEqual(resp.status_code, 200)

        # 2 tracked days with total 4000 kcal -> avg = 2000.0 kcal/day
        self.assertEqual(resp.context['days_tracked'], 2)
        self.assertEqual(resp.context['total_range_calories'], Decimal('4000.00'))
        self.assertEqual(resp.context['avg_daily_calories'], 2000.0)

        # Weight change: 76.5 - 78.0 = -1.5 kg (loss)
        self.assertEqual(resp.context['latest_weight'], Decimal('76.50'))
        self.assertEqual(resp.context['weight_change'], Decimal('1.50'))
        self.assertEqual(resp.context['weight_change_direction'], 'loss')

    def test_date_filtering_7_days_30_days_custom(self):
        """Date filtering correctly restricts aggregated entries to requested range"""
        self.client_a.login(username='dan', password='Password123!')

        # Entry 15 days ago: 500 kcal
        FoodEntry.objects.create(
            user=self.user_a,
            date=self.today - timedelta(days=15),
            meal_category='Lunch',
            food_name='Old Salad',
            quantity=Decimal('1.00'),
            calories=Decimal('500.00')
        )
        # Entry today: 1000 kcal
        FoodEntry.objects.create(
            user=self.user_a,
            date=self.today,
            meal_category='Dinner',
            food_name='Steak Dinner',
            quantity=Decimal('1.00'),
            calories=Decimal('1000.00')
        )

        # Last 7 Days: Should only include today's entry (1000 kcal)
        resp_7 = self.client_a.get(reverse('progress') + '?range=7')
        self.assertEqual(resp_7.context['total_range_calories'], Decimal('1000.00'))
        self.assertEqual(resp_7.context['days_tracked'], 1)

        # Last 30 Days: Should include both entries (1500 kcal)
        resp_30 = self.client_a.get(reverse('progress') + '?range=30')
        self.assertEqual(resp_30.context['total_range_calories'], Decimal('1500.00'))
        self.assertEqual(resp_30.context['days_tracked'], 2)

        # Custom Range: Exactly 15 days ago
        custom_date = (self.today - timedelta(days=15)).isoformat()
        resp_custom = self.client_a.get(reverse('progress') + f"?range=custom&start_date={custom_date}&end_date={custom_date}")
        self.assertEqual(resp_custom.context['total_range_calories'], Decimal('500.00'))
        self.assertEqual(resp_custom.context['days_tracked'], 1)

    def test_empty_states_when_no_user_data(self):
        """Displays clear empty states and does NOT generate sample/fake chart data"""
        self.client_b.login(username='eve', password='Password123!')

        resp = self.client_b.get(reverse('progress'))
        self.assertEqual(resp.status_code, 200)

        # Verified zero actual user data
        self.assertEqual(resp.context['days_tracked'], 0)
        self.assertEqual(resp.context['total_range_calories'], Decimal('0.00'))
        self.assertEqual(resp.context['avg_daily_calories'], 0)
        self.assertFalse(resp.context['has_calorie_data'])
        self.assertFalse(resp.context['has_macro_data'])
        self.assertFalse(resp.context['has_weight_data'])
        self.assertFalse(resp.context['has_weight_records'])

        # Response HTML contains empty state messaging
        self.assertContains(resp, 'No Weight Records Logged')
        self.assertContains(resp, 'No Diary Entries in Selected Range')
        self.assertContains(resp, 'No Macronutrients Recorded')
