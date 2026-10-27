from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from food_diary.models import FoodEntry
from nutrition.models import FoodItem
from recipes.models import SavedMeal, SavedMealItem

class Stage3FeaturesTests(TestCase):
    def setUp(self):
        self.client_a = Client()
        self.user_a = User.objects.create_user('alice', 'alice@fitora.local', 'Password123!')
        self.profile_a = Profile.objects.get_or_create(user=self.user_a)[0]
        self.profile_a.daily_calorie_goal = Decimal('1800.00')
        self.profile_a.save()

        self.client_b = Client()
        self.user_b = User.objects.create_user('bob', 'bob@fitora.local', 'Password123!')

        self.today = timezone.now().date()

        # Create starter foods
        self.idli = FoodItem.objects.create(
            name='Idli (Steamed Rice & Lentil Cake)',
            serving_size=Decimal('1.00'),
            serving_unit='piece',
            serving_description='1 piece (~40g)',
            calories=Decimal('58.00'),
            protein=Decimal('2.00'),
            carbohydrates=Decimal('12.00'),
            fat=Decimal('0.20'),
            data_source='Fitora Starter Database (Estimated nutrition; non-medical)',
            is_verified=True
        )

        self.egg = FoodItem.objects.create(
            name='Boiled Egg',
            serving_size=Decimal('1.00'),
            serving_unit='large egg',
            serving_description='1 large egg (~50g)',
            calories=Decimal('78.00'),
            protein=Decimal('6.30'),
            carbohydrates=Decimal('0.60'),
            fat=Decimal('5.30'),
            data_source='Fitora Starter Database (Estimated nutrition; non-medical)',
            is_verified=True
        )

    def test_case_insensitive_food_search(self):
        """Food search API returns matching starter foods case-insensitively with nutrition"""
        self.client_a.login(username='alice', password='Password123!')

        resp = self.client_a.get(reverse('food_search_api'), {'query': 'IDLI'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        results = data['results']
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]['name'], 'Idli (Steamed Rice & Lentil Cake)')
        self.assertEqual(results[0]['calories'], 58.0)
        self.assertEqual(results[0]['serving_description'], '1 piece (~40g)')

    def test_server_side_validation_empty_food_name(self):
        """Server-side validation rejects empty food name"""
        self.client_a.login(username='alice', password='Password123!')
        resp = self.client_a.post(reverse('add_entry'), {
            'date': self.today.isoformat(),
            'meal_category': 'Breakfast',
            'food_name': '',  # Empty
            'quantity': '1',
            'serving_amount': '100',
            'serving_unit': 'g',
            'calories': '100.00'
        })
        self.assertEqual(resp.status_code, 200)  # Re-renders form with error
        self.assertFormError(resp.context['form'], 'food_name', 'Food name is required.')

    def test_server_side_validation_zero_and_negative_quantity(self):
        """Server-side validation rejects zero or negative quantity"""
        self.client_a.login(username='alice', password='Password123!')
        resp = self.client_a.post(reverse('add_entry'), {
            'date': self.today.isoformat(),
            'meal_category': 'Breakfast',
            'food_name': 'Banana',
            'quantity': '0',  # Zero
            'serving_amount': '100',
            'serving_unit': 'g',
            'calories': '105.00'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp.context['form'], 'quantity', 'Serving quantity must be greater than zero.')

        resp_neg = self.client_a.post(reverse('add_entry'), {
            'date': self.today.isoformat(),
            'meal_category': 'Breakfast',
            'food_name': 'Banana',
            'quantity': '-2',  # Negative
            'serving_amount': '100',
            'serving_unit': 'g',
            'calories': '105.00'
        })
        self.assertEqual(resp_neg.status_code, 200)
        self.assertFormError(resp_neg.context['form'], 'quantity', 'Serving quantity must be greater than zero.')

    def test_negative_calorie_tracking_when_goal_exceeded(self):
        """Calories remaining becomes negative and clearly flagged when goal is exceeded"""
        self.client_a.login(username='alice', password='Password123!')

        # Goal is 1800. Log entries totaling 2200 kcal.
        FoodEntry.objects.create(
            user=self.user_a,
            date=self.today,
            meal_category='Lunch',
            food_name='Feast',
            quantity=Decimal('1.00'),
            calories=Decimal('2200.00')
        )

        resp = self.client_a.get(reverse('food_diary'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['calories_remaining'], Decimal('-400.00'))
        self.assertTrue(resp.context['goal_exceeded'])
        self.assertEqual(resp.context['exceeded_by'], Decimal('400.00'))
        self.assertContains(resp, 'exceeded by <strong>400.00 kcal</strong>')

        # Check dashboard also reflects this
        dash_resp = self.client_a.get(reverse('dashboard'))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertEqual(dash_resp.context['calories_remaining'], Decimal('-400.00'))
        self.assertTrue(dash_resp.context['goal_exceeded'])
        self.assertEqual(dash_resp.context['exceeded_by'], Decimal('400.00'))

    def test_saved_meal_crud_and_logging_to_diary(self):
        """Full lifecycle of SavedMeal: create, add items, log to diary, and verify entries"""
        self.client_a.login(username='alice', password='Password123!')

        # 1. Create Saved Meal
        create_resp = self.client_a.post(reverse('create_saved_meal'), {
            'name': 'Power Breakfast Combo',
            'description': '2 Boiled Eggs and 2 Idlis'
        })
        self.assertEqual(create_resp.status_code, 302)
        saved_meal = SavedMeal.objects.get(name='Power Breakfast Combo', user=self.user_a)

        # 2. Add Egg item (qty = 2)
        item1_resp = self.client_a.post(reverse('saved_meal_detail', args=[saved_meal.id]), {
            'food_item': self.egg.id,
            'quantity': '2.0',
            'serving_amount': '50',
            'serving_unit': 'egg'
        })
        self.assertEqual(item1_resp.status_code, 302)

        # 3. Add Idli item (qty = 2)
        item2_resp = self.client_a.post(reverse('saved_meal_detail', args=[saved_meal.id]), {
            'food_item': self.idli.id,
            'quantity': '2.0',
            'serving_amount': '40',
            'serving_unit': 'piece'
        })
        self.assertEqual(item2_resp.status_code, 302)

        saved_meal.refresh_from_db()
        self.assertEqual(saved_meal.items.count(), 2)

        # Nutrition calculation:
        # Egg: 78 kcal * 2 = 156 kcal, 6.3g protein * 2 = 12.6g
        # Idli: 58 kcal * 2 = 116 kcal, 2g protein * 2 = 4.0g
        # Total: 156 + 116 = 272 kcal, 16.6g protein
        self.assertEqual(saved_meal.total_calories, Decimal('272.00'))
        self.assertEqual(saved_meal.total_protein, Decimal('16.60'))

        # 4. Log Saved Meal to Food Diary for Breakfast
        log_resp = self.client_a.post(reverse('log_saved_meal_to_diary', args=[saved_meal.id]), {
            'meal_category': 'Breakfast',
            'date': self.today.isoformat()
        })
        self.assertEqual(log_resp.status_code, 302)

        # Verify FoodEntry rows created in DB
        entries = FoodEntry.objects.filter(user=self.user_a, date=self.today, meal_category='Breakfast')
        self.assertEqual(entries.count(), 2)
        egg_entry = entries.filter(food_name__icontains='Boiled Egg').first()
        self.assertIsNotNone(egg_entry)
        self.assertEqual(egg_entry.quantity, Decimal('2.00'))
        self.assertEqual(egg_entry.calories, Decimal('156.00'))

        # 5. Delete individual item
        egg_saved_item = saved_meal.items.filter(food_item=self.egg).first()
        del_item_resp = self.client_a.post(reverse('delete_saved_meal_item', args=[saved_meal.id, egg_saved_item.id]))
        self.assertEqual(del_item_resp.status_code, 302)
        self.assertEqual(saved_meal.items.count(), 1)

        # 6. Delete saved meal
        del_meal_resp = self.client_a.post(reverse('delete_saved_meal', args=[saved_meal.id]))
        self.assertEqual(del_meal_resp.status_code, 302)
        self.assertFalse(SavedMeal.objects.filter(id=saved_meal.id).exists())

    def test_saved_meal_ownership_isolation(self):
        """User B cannot view, edit, add items to, or delete User A's saved meal"""
        # User A creates meal
        meal_a = SavedMeal.objects.create(
            user=self.user_a,
            name='Secret Meal A',
            description='Private'
        )

        self.client_b.login(username='bob', password='Password123!')

        # Bob attempts to view Alice's meal -> 404
        resp_detail = self.client_b.get(reverse('saved_meal_detail', args=[meal_a.id]))
        self.assertEqual(resp_detail.status_code, 404)

        # Bob attempts to edit Alice's meal -> 404
        resp_edit = self.client_b.post(reverse('edit_saved_meal', args=[meal_a.id]), {
            'name': 'Hacked Name'
        })
        self.assertEqual(resp_edit.status_code, 404)

        # Bob attempts to delete Alice's meal -> 404
        resp_del = self.client_b.post(reverse('delete_saved_meal', args=[meal_a.id]))
        self.assertEqual(resp_del.status_code, 404)
        self.assertTrue(SavedMeal.objects.filter(id=meal_a.id).exists())
