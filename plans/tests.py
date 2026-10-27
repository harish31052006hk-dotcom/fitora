from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from .models import WeeklyPlan
from .services import _fallback_plan


class WeeklyPlanPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('planner', 'planner@example.test', 'PlanPass123!')
        self.profile = Profile.objects.get(user=self.user)
        self.url = reverse('weekly_plan')

    def test_weekly_plan_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_empty_page_shows_preferences_and_generate_action(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Build my weekly plan')
        self.assertContains(response, 'Food preference')
        self.assertIsNone(response.context['plan'])

    @patch('plans.views.generate_weekly_plan')
    def test_post_generates_and_saves_a_user_scoped_plan(self, mock_generate):
        self.client.force_login(self.user)
        plan_data = {
            'title': 'A simple week',
            'summary': 'Flexible plan.',
            'primary_focus': 'Consistency',
            'daily_target': {'calories_kcal': 2000, 'protein_g': 120, 'carbs_g': 220, 'fat_g': 65},
            'days': [], 'prep_tips': [], 'shopping_list': [], 'notes': 'Estimates are approximate.',
        }
        mock_generate.return_value = (plan_data, 'ai', '')
        response = self.client.post(self.url, {
            'goal': 'maintenance', 'diet': 'vegetarian', 'training_days': '3',
            'budget': 'moderate', 'prep_time': '30', 'foods_to_avoid': 'mushrooms',
        })
        self.assertEqual(response.status_code, 302)
        plan = WeeklyPlan.objects.get(user=self.user)
        self.assertEqual(plan.generation_source, 'ai')
        self.assertEqual(plan.preferences['diet'], 'vegetarian')
        self.assertEqual(plan.preferences['foods_to_avoid'], 'mushrooms')
        self.assertEqual(plan.week_start, timezone.localdate() - timedelta(days=timezone.localdate().weekday()))
        mock_generate.assert_called_once()

    def test_fallback_plan_has_seven_days_and_profile_targets(self):
        data = _fallback_plan(self.profile, {'goal': 'general_health', 'diet': 'vegetarian', 'training_days': '3'}, '')
        self.assertEqual(len(data['days']), 7)
        self.assertEqual(data['daily_target']['calories_kcal'], self.profile.daily_calorie_goal)
        self.assertEqual(data['days'][0]['day'], 'Monday')
        self.assertTrue(all(len(day['meals']) >= 3 for day in data['days']))
