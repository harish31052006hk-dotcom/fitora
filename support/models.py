import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class FAQ(models.Model):
    """
    Frequently Asked Questions knowledge base stored in PostgreSQL.
    Retrieved both by users on the FAQ page and by the AI Assistant before answering queries.
    """
    CATEGORY_CHOICES = [
        ('Getting Started', 'Getting Started'),
        ('Food Diary', 'Food Diary & Tracking'),
        ('Nutrition & Goals', 'Nutrition & Goals'),
        ('Recipes', 'Recipes & Meals'),
        ('Technical & Account', 'Technical & Account'),
    ]

    question = models.CharField(max_length=300, unique=True)
    answer = models.TextField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='Getting Started')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return f"[{self.category}] {self.question}"


class SupportTicket(models.Model):
    """
    User technical and nutrition support tickets stored in PostgreSQL.
    Can be created via the web portal or automatically triggered by the AI assistant.
    """
    STATUS_OPEN = 'Open'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_RESOLVED = 'Resolved'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
    ]

    CATEGORY_CHOICES = [
        ('Technical', 'Technical Issue / Bug'),
        ('Nutrition Data', 'Nutrition Data Inquiry'),
        ('Account', 'Account & Security'),
        ('Feature Request', 'Feature Request'),
        ('General Support', 'General Support'),
    ]

    ticket_id = models.CharField(max_length=30, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_tickets')
    contact_email = models.EmailField(blank=True, default='')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Technical')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        user_str = self.user.username if self.user else self.contact_email or 'Guest'
        return f"Ticket {self.ticket_id} [{self.status}] - {self.subject} ({user_str})"

    @classmethod
    def generate_ticket_id(cls):
        """Generates a clean human-readable ticket ID like FIT-20261027-A1B2."""
        date_str = timezone.now().strftime('%Y%m%d')
        random_suffix = uuid.uuid4().hex[:5].upper()
        return f"FIT-{date_str}-{random_suffix}"
