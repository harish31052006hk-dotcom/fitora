from decimal import Decimal
from unittest.mock import patch
import requests
from django.test import TestCase
from nutrition.api_client import NutritionAPIClient
from nutrition.models import FoodItem

class ThirdPartyNutritionAPITests(TestCase):
    def setUp(self):
        # Create verified fallback food in database
        self.verified_food = FoodItem.objects.create(
            name='Fresh Chicken Breast',
            serving_size=Decimal('100.00'),
            calories=Decimal('165.00'),
            protein=Decimal('31.00'),
            carbohydrates=Decimal('0.00'),
            fat=Decimal('3.60'),
            is_verified=True
        )
        self.client = NutritionAPIClient()

    @patch('requests.get')
    def test_nutrition_api_timeout_fallback(self, mock_get):
        # Simulate requests timeout
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out after 4 seconds")

        result = self.client.search_food('Chicken')
        self.assertTrue(result['success'])
        self.assertTrue(result['is_fallback'])
        self.assertEqual(result['source'], 'fallback')
        self.assertIn("unavailable or timed out", result['message'])
        self.assertTrue(len(result['items']) > 0)
        self.assertEqual(result['items'][0]['name'], 'Fresh Chicken Breast')

    @patch('requests.get')
    def test_nutrition_api_rate_limit_429_fallback(self, mock_get):
        # Simulate HTTP 429 Too Many Requests
        mock_response = requests.Response()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        result = self.client.search_food('Chicken')
        self.assertTrue(result['success'])
        self.assertTrue(result['is_fallback'])
        self.assertEqual(result['source'], 'fallback')

    @patch('requests.get')
    def test_nutrition_api_network_error_fallback(self, mock_get):
        # Simulate network failure / connection aborted
        mock_get.side_effect = requests.exceptions.ConnectionError("Network unreachable")

        result = self.client.search_food('Chicken')
        self.assertTrue(result['success'])
        self.assertTrue(result['is_fallback'])
        self.assertEqual(result['source'], 'fallback')
