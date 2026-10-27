from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import Profile

class UserAuthenticationTests(TestCase):
    """
    Tests for User Registration, Login, Logout, and Access Controls.
    """
    def setUp(self):
        self.client = Client()
        self.username = 'testathlete'
        self.password = 'StrongSecretPass123!'
        self.email = 'athlete@fitora.local'
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email=self.email
        )

    def test_user_registration(self):
        response = self.client.post(reverse('register'), {
            'username': 'newrunner',
            'email': 'runner@fitora.local',
            'first_name': 'New',
            'last_name': 'Runner',
            'password1': 'SafePassRunner88!',
            'password2': 'SafePassRunner88!',
        })
        self.assertEqual(response.status_code, 302) # Redirects to dashboard upon login
        self.assertTrue(User.objects.filter(username='newrunner').exists())
        new_user = User.objects.get(username='newrunner')
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertEqual(new_user.profile.daily_calorie_goal, 2000)

    def test_user_login_and_logout(self):
        # Successful login
        login_resp = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password,
        })
        self.assertEqual(login_resp.status_code, 302)

        # Logout
        logout_resp = self.client.get(reverse('logout'))
        self.assertEqual(logout_resp.status_code, 302)

    def test_unauthorized_access_prevention(self):
        # Protected pages must redirect unauthenticated visitors to login
        protected_urls = [
            reverse('dashboard'),
            reverse('food_diary'),
            reverse('recipe_list'),
            reverse('progress'),
            reverse('profile'),
        ]
        for url in protected_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn(reverse('login'), resp.url)

    def test_public_pages_accessible_without_auth(self):
        # Public pages must remain accessible to everyone
        public_urls = [
            reverse('home'),
            reverse('faq'),
            reverse('error_guide'),
            reverse('assistant_page'),
            reverse('health_check'),
        ]
        for url in public_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)

    def test_profile_goals_update(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.post(reverse('profile'), {
            'daily_calorie_goal': 2400,
            'daily_protein_goal': 175,
            'daily_carbs_goal': 260,
            'daily_fat_goal': 70,
            'current_weight': '78.50',
            'target_weight': '75.00',
        })
        self.assertEqual(resp.status_code, 302)
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.daily_calorie_goal, 2400)
        self.assertEqual(profile.daily_protein_goal, 175)
