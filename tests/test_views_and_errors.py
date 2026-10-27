from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from support.views import custom_404_view, custom_500_view

class ViewsAndErrorPagesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

    def test_custom_404_page_on_invalid_url(self):
        # Visiting an invalid route must return 404 and render custom template
        resp = self.client.get('/this-url-definitely-does-not-exist-in-fitora/')
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed(resp, '404.html')
        self.assertContains(resp, 'Page Not Found', status_code=404)
        self.assertContains(resp, 'Ask AI', status_code=404)

    def test_custom_500_error_handler(self):
        request = self.factory.get('/simulate-500/')
        resp = custom_500_view(request)
        self.assertEqual(resp.status_code, 500)
        self.assertIn(b'Internal Server Error', resp.content)
        self.assertIn(b'Ask AI', resp.content)

    def test_health_check_endpoint(self):
        resp = self.client.get(reverse('health_check'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['app'], 'Fitora')
        self.assertIn('services', data)
        self.assertEqual(data['services']['relational_database']['status'], 'connected')
        self.assertIn('response_time_ms', data)

    def test_app001_demo_page(self):
        resp = self.client.get(reverse('demo_app001'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'APP-001')
        self.assertContains(resp, 'Fitora Application Event')
