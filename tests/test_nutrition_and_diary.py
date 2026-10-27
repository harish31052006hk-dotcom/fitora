from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from food_diary.models import FoodEntry
from nutrition.models import FoodItem
from accounts.models import Profile

class NutritionAndFoodDiaryTests(TestCase):
    def setUp(self):
        self.client_a = Client()
        self.user_a = User.objects.create_user('usera', 'usera@fitora.local', 'Password123!')
        self.profile_a = Profile.objects.get_or_create(user=self.user_a, defaults={'daily_calorie_goal': 2000})[0]

        self.client_b = Client()
        self.user_b = User.objects.create_user('userb', 'userb@fitora.local', 'Password123!')

        self.today = timezone.now().date()

    def test_serving_size_calculation_accuracy(self):
        # 100g of food has 150 kcal. A 200g serving should contribute exactly 300 kcal.
        food = FoodItem.objects.create(
            name='Energy Bar',
            serving_size=Decimal('100.00'),
            serving_unit='g',
            calories=Decimal('150.00'),
            protein=Decimal('10.00'),
            carbohydrates=Decimal('20.00'),
            fat=Decimal('5.00')
        )
        calculated = food.calculate_nutrition(Decimal('200.00'))
        self.assertEqual(calculated['calories'], Decimal('300.00'))
        self.assertEqual(calculated['protein'], Decimal('20.00'))
        self.assertEqual(calculated['carbohydrates'], Decimal('40.00'))
        self.assertEqual(calculated['fat'], Decimal('10.00'))

    def test_food_entry_creation_and_totals(self):
        self.client_a.login(username='usera', password='Password123!')

        # Add breakfast item
        resp = self.client_a.post(reverse('add_entry'), {
            'date': self.today.isoformat(),
            'meal_category': 'Breakfast',
            'food_name': 'Oatmeal with Almond Milk',
            'serving_amount': '150.00',
            'serving_unit': 'g',
            'calories': '220.00',
            'protein': '8.00',
            'carbohydrates': '38.00',
            'fat': '4.50'
        })
        self.assertEqual(resp.status_code, 302)

        # Add lunch item
        self.client_a.post(reverse('add_entry'), {
            'date': self.today.isoformat(),
            'meal_category': 'Lunch',
            'food_name': 'Grilled Salmon',
            'serving_amount': '200.00',
            'serving_unit': 'g',
            'calories': '416.00',
            'protein': '44.00',
            'carbohydrates': '0.00',
            'fat': '26.00'
        })

        # Check total entries
        entries = FoodEntry.objects.filter(user=self.user_a, date=self.today)
        self.assertEqual(entries.count(), 2)

        total_calories = sum((e.calories for e in entries), Decimal('0.00'))
        self.assertEqual(total_calories, Decimal('636.00'))

        # Check diary view
        diary_resp = self.client_a.get(reverse('food_diary'))
        self.assertEqual(diary_resp.status_code, 200)
        self.assertEqual(diary_resp.context['total_calories'], Decimal('636.00'))
        # Calories remaining = 2000 - 636 = 1364
        self.assertEqual(diary_resp.context['calories_remaining'], Decimal('1364.00'))

    def test_food_entry_editing(self):
        self.client_a.login(username='usera', password='Password123!')
        entry = FoodEntry.objects.create(
            user=self.user_a,
            date=self.today,
            meal_category='Dinner',
            food_name='Brown Rice',
            serving_amount=Decimal('100.00'),
            serving_unit='g',
            calories=Decimal('123.00')
        )
        # Edit entry to 150g and 184.50 kcal
        edit_resp = self.client_a.post(reverse('edit_entry', args=[entry.id]), {
            'date': self.today.isoformat(),
            'meal_category': 'Dinner',
            'food_name': 'Brown Rice (Cooked)',
            'serving_amount': '150.00',
            'serving_unit': 'g',
            'calories': '184.50',
            'protein': '4.00',
            'carbohydrates': '38.00',
            'fat': '1.50'
        })
        self.assertEqual(edit_resp.status_code, 302)
        entry.refresh_from_db()
        self.assertEqual(entry.calories, Decimal('184.50'))
        self.assertEqual(entry.food_name, 'Brown Rice (Cooked)')

    def test_food_entry_deletion(self):
        self.client_a.login(username='usera', password='Password123!')
        entry = FoodEntry.objects.create(
            user=self.user_a,
            date=self.today,
            meal_category='Snacks',
            food_name='Apple',
            serving_amount=Decimal('120.00'),
            serving_unit='g',
            calories=Decimal('65.00')
        )
        del_resp = self.client_a.post(reverse('delete_entry', args=[entry.id]))
        self.assertEqual(del_resp.status_code, 302)
        self.assertFalse(FoodEntry.objects.filter(id=entry.id).exists())

    def test_user_data_isolation_cannot_access_other_user_entry(self):
        # Create entry belonging to User A
        entry_a = FoodEntry.objects.create(
            user=self.user_a,
            date=self.today,
            meal_category='Lunch',
            food_name='Private Meal',
            serving_amount=Decimal('100.00'),
            calories=Decimal('200.00')
        )
        # User B logs in
        self.client_b.login(username='userb', password='Password123!')

        # User B attempts to edit User A's entry -> Must return 404
        edit_attempt = self.client_b.get(reverse('edit_entry', args=[entry_a.id]))
        self.assertEqual(edit_attempt.status_code, 404)

        # User B attempts to delete User A's entry -> Must return 404
        delete_attempt = self.client_b.post(reverse('delete_entry', args=[entry_a.id]))
        self.assertEqual(delete_attempt.status_code, 404)
        self.assertTrue(FoodEntry.objects.filter(id=entry_a.id).exists())
