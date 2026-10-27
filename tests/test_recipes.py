from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from recipes.models import Recipe, RecipeIngredient
from food_diary.models import FoodEntry

class RecipeAndMealManagementTests(TestCase):
    def setUp(self):
        self.client_a = Client()
        self.user_a = User.objects.create_user('chef', 'chef@fitora.local', 'ChefPass123!')
        self.client_a.login(username='chef', password='ChefPass123!')

        self.client_b = Client()
        self.user_b = User.objects.create_user('rival', 'rival@fitora.local', 'ChefPass123!')

    def test_recipe_creation_and_per_serving_calculation(self):
        # Create recipe for 2 servings
        recipe = Recipe.objects.create(
            user=self.user_a,
            name='High Protein Chicken Bowl',
            description='Quick post workout meal',
            servings=2
        )
        # Ingredient 1: Chicken (300 kcal, 60g protein, 0g carbs, 6g fat)
        RecipeIngredient.objects.create(
            recipe=recipe,
            food_name='Grilled Chicken',
            amount=Decimal('200.00'),
            unit='g',
            calories=Decimal('300.00'),
            protein=Decimal('60.00'),
            carbohydrates=Decimal('0.00'),
            fat=Decimal('6.00')
        )
        # Ingredient 2: Rice (240 kcal, 6g protein, 50g carbs, 2g fat)
        RecipeIngredient.objects.create(
            recipe=recipe,
            food_name='Cooked Jasmine Rice',
            amount=Decimal('200.00'),
            unit='g',
            calories=Decimal('240.00'),
            protein=Decimal('6.00'),
            carbohydrates=Decimal('50.00'),
            fat=Decimal('2.00')
        )

        # Total recipe verification
        self.assertEqual(recipe.total_calories, Decimal('540.00'))
        self.assertEqual(recipe.total_protein, Decimal('66.00'))
        self.assertEqual(recipe.total_carbohydrates, Decimal('50.00'))
        self.assertEqual(recipe.total_fat, Decimal('8.00'))

        # Per serving verification (divided by 2 portions)
        self.assertEqual(recipe.per_serving_calories, Decimal('270.00'))
        self.assertEqual(recipe.per_serving_protein, Decimal('33.00'))
        self.assertEqual(recipe.per_serving_carbohydrates, Decimal('25.00'))
        self.assertEqual(recipe.per_serving_fat, Decimal('4.00'))

    def test_log_recipe_to_diary(self):
        recipe = Recipe.objects.create(
            user=self.user_a,
            name='Avocado Toast',
            servings=1
        )
        RecipeIngredient.objects.create(
            recipe=recipe,
            food_name='Avocado & Sourdough',
            amount=Decimal('150.00'),
            calories=Decimal('350.00'),
            protein=Decimal('8.00'),
            carbohydrates=Decimal('35.00'),
            fat=Decimal('18.00')
        )

        today_str = timezone.now().date().isoformat()
        log_resp = self.client_a.post(reverse('log_recipe_to_diary', args=[recipe.id]), {
            'date': today_str,
            'meal_category': 'Breakfast',
            'servings': '1.0'
        })
        self.assertEqual(log_resp.status_code, 302)

        # Verify entry created in diary
        entry = FoodEntry.objects.filter(user=self.user_a, meal_category='Breakfast').first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.calories, Decimal('350.00'))
        self.assertIn('Avocado Toast', entry.food_name)

    def test_recipe_isolation_prevention(self):
        recipe = Recipe.objects.create(
            user=self.user_a,
            name='Secret Family Recipe',
            servings=4
        )
        self.client_b.login(username='rival', password='ChefPass123!')

        # Rival user cannot view, edit, or delete chef's recipe
        detail_resp = self.client_b.get(reverse('recipe_detail', args=[recipe.id]))
        self.assertEqual(detail_resp.status_code, 404)

        edit_resp = self.client_b.get(reverse('edit_recipe', args=[recipe.id]))
        self.assertEqual(edit_resp.status_code, 404)

        del_resp = self.client_b.post(reverse('delete_recipe', args=[recipe.id]))
        self.assertEqual(del_resp.status_code, 404)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
