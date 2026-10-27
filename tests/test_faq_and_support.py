from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from support.models import FAQ, SupportTicket

class FAQAndSupportTicketTests(TestCase):
    def setUp(self):
        self.client_a = Client()
        self.user_a = User.objects.create_user('member', 'member@fitora.local', 'MemberPass123!')
        self.client_a.login(username='member', password='MemberPass123!')

        self.client_b = Client()
        self.user_b = User.objects.create_user('other', 'other@fitora.local', 'OtherPass123!')

        # Create sample FAQs
        self.faq1 = FAQ.objects.create(
            question='How do I set my calorie goal?',
            answer='Go to your Profile and update your target energy intake.',
            category='Nutrition & Goals',
            order=1
        )
        self.faq2 = FAQ.objects.create(
            question='How do I add food to my diary?',
            answer='Use the + Add Food button in the food diary view.',
            category='Food Diary',
            order=2
        )
        self.faq3 = FAQ.objects.create(
            question='What does error code APP-001 mean?',
            answer='APP-001 is a Fitora application-specific code indicating a local nutrition calculation issue or fallback.',
            category='Technical & Account',
            order=3
        )

    def test_faq_database_retrieval(self):
        resp = self.client_a.get(reverse('faq'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'How do I set my calorie goal?')
        self.assertContains(resp, 'How do I add food to my diary?')
        self.assertContains(resp, 'What does error code APP-001 mean?')

    def test_faq_search(self):
        search_resp = self.client_a.get(reverse('faq') + '?q=calorie')
        self.assertEqual(search_resp.status_code, 200)
        faqs_in_context = list(search_resp.context['faqs'])
        self.assertIn(self.faq1, faqs_in_context)
        self.assertNotIn(self.faq2, faqs_in_context)

    def test_faq_category_filter(self):
        cat_resp = self.client_a.get(reverse('faq') + '?category=Food Diary')
        self.assertEqual(cat_resp.status_code, 200)
        faqs_in_context = list(cat_resp.context['faqs'])
        self.assertIn(self.faq2, faqs_in_context)
        self.assertNotIn(self.faq1, faqs_in_context)

    def test_support_ticket_creation_and_persistence(self):
        resp = self.client_a.post(reverse('support_tickets'), {
            'subject': 'Food search timeout question',
            'category': 'Technical',
            'description': 'I noticed food search took 3 seconds and switched to offline database.',
            'contact_email': 'member@fitora.local'
        })
        self.assertEqual(resp.status_code, 302)

        ticket = SupportTicket.objects.filter(user=self.user_a).first()
        self.assertIsNotNone(ticket)
        self.assertTrue(ticket.ticket_id.startswith('FIT-'))
        self.assertEqual(ticket.subject, 'Food search timeout question')
        self.assertEqual(ticket.status, SupportTicket.STATUS_OPEN)

    def test_support_ticket_isolation(self):
        ticket = SupportTicket.objects.create(
            ticket_id=SupportTicket.generate_ticket_id(),
            user=self.user_a,
            subject='Confidential Account Issue',
            description='Sensitive detail',
            status='Open'
        )

        # Other user logs in
        self.client_b.login(username='other', password='OtherPass123!')
        resp = self.client_b.get(reverse('ticket_detail', args=[ticket.ticket_id]))
        self.assertEqual(resp.status_code, 404)
