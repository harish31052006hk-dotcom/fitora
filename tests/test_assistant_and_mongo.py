import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from support.models import FAQ, SupportTicket
from food_diary.models import FoodEntry
from accounts.models import Profile
from assistant.service import FitoraAssistantService

class AIAssistantAndMongoDBTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('fitfan', 'fitfan@fitora.local', 'FitFanPass123!')
        self.profile = Profile.objects.get_or_create(user=self.user)[0]
        self.profile.daily_calorie_goal = 2200
        self.profile.save()

        # Seed test FAQ
        FAQ.objects.create(
            question='How do I track protein?',
            answer='Each food logged tracks grams of protein against your daily target.',
            category='Nutrition & Goals'
        )

    def test_faq_retrieval_before_answering(self):
        service = FitoraAssistantService()
        result = service.process_message("How do I track protein in Fitora?", user=self.user)
        self.assertEqual(result['source'], 'faq_database')
        self.assertIn('How do I track protein?', result['response'])
        self.assertIn('grams of protein against your daily target', result['response'])

    def test_error_code_explanation_http_429(self):
        service = FitoraAssistantService()
        result = service.process_message("I am seeing HTTP 429 error code, what does it mean?", user=self.user)
        self.assertEqual(result['source'], 'error_guide')
        self.assertIn('HTTP 429', result['response'])
        self.assertIn('Too Many Requests', result['response'])
        self.assertIn('Recommended Troubleshooting Steps', result['response'])

    def test_error_code_explanation_app_001(self):
        service = FitoraAssistantService()
        result = service.process_message("Explain what APP-001 means", user=self.user)
        self.assertEqual(result['source'], 'error_guide')
        self.assertIn('APP-001', result['response'])
        self.assertIn('Fitora Application-Specific Error', result['response'])

    def test_personal_calorie_data_retrieval(self):
        today = timezone.now().date()
        FoodEntry.objects.create(
            user=self.user,
            date=today,
            meal_category='Breakfast',
            food_name='Oatmeal & Eggs',
            serving_amount=Decimal('150.00'),
            calories=Decimal('450.00'),
            protein=Decimal('25.00')
        )

        service = FitoraAssistantService()
        result = service.process_message("How many calories have I consumed today?", user=self.user)
        self.assertEqual(result['source'], 'user_nutrition')
        self.assertIn('450.00 kcal', result['response']) # Consumed
        self.assertIn('1750.00 kcal', result['response']) # Remaining: 2200 - 450 = 1750
        self.assertIn('**Daily Goal:** 2200 kcal', result['response'])

    def test_support_ticket_creation_via_ai(self):
        service = FitoraAssistantService()
        result = service.process_message("Please open a support ticket for my connection issue", user=self.user)
        self.assertEqual(result['source'], 'ticket_system')
        self.assertTrue(result['ticket_created'])
        self.assertIsNotNone(result['ticket_id'])
        self.assertTrue(result['ticket_id'].startswith('FIT-'))
        # Check database record
        ticket = SupportTicket.objects.get(ticket_id=result['ticket_id'])
        self.assertEqual(ticket.user, self.user)
        self.assertEqual(ticket.status, 'Open')

    def test_ai_api_failure_fallback_mode(self):
        # Force invalid API URL / timeout simulation
        service = FitoraAssistantService()
        service.api_key = 'fake-key'
        service.api_url = 'https://invalid-nonexistent-domain.fitora.ai'
        
        # Must fall back gracefully to FAQ knowledge base without crashing
        result = service.process_message("How do I track protein?", user=self.user)
        self.assertIn(result['source'], ['faq_database', 'fallback_faq'])
        self.assertIn('How do I track protein?', result['response'])

    @patch('assistant.views.log_chat_interaction')
    def test_chat_api_endpoint_with_mongo_mock(self, mock_mongo_log):
        mock_mongo_log.return_value = {'saved': True, 'id': 'mock_doc_id_1234'}
        self.client.login(username='fitfan', password='FitFanPass123!')

        resp = self.client.post(
            reverse('assistant_chat_api'),
            data=json.dumps({'message': 'Explain error 500', 'conversation_id': 'test_conv_1'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('HTTP 500', data['response'])
        self.assertTrue(data['mongo_logged'])
        mock_mongo_log.assert_called_once()

    @patch('assistant.views.log_user_feedback')
    def test_feedback_api_endpoint_with_mongo_mock(self, mock_mongo_feedback):
        mock_mongo_feedback.return_value = {'saved': True, 'id': 'mock_feed_id_5678'}
        resp = self.client.post(
            reverse('assistant_feedback_api'),
            data=json.dumps({'conversation_id': 'test_conv_1', 'rating': 'helpful', 'comment': 'Great answer!'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['saved_to_mongo'])
        mock_mongo_feedback.assert_called_once()
