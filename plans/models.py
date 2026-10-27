from django.conf import settings
from django.db import models


class WeeklyPlan(models.Model):
    """A user's saved, editable-preference weekly meal and movement plan."""
    SOURCE_AI = 'ai'
    SOURCE_TEMPLATE = 'template'
    SOURCE_CHOICES = [
        (SOURCE_AI, 'AI generated'),
        (SOURCE_TEMPLATE, 'Template fallback'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='weekly_plans',
    )
    week_start = models.DateField(db_index=True, help_text='Monday of the planned week')
    preferences = models.JSONField(default=dict, blank=True)
    plan_data = models.JSONField(default=dict, blank=True)
    generation_source = models.CharField(max_length=12, choices=SOURCE_CHOICES, default=SOURCE_TEMPLATE)
    generation_note = models.CharField(max_length=240, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-week_start', '-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'week_start'], name='unique_weekly_plan_per_user_week'),
        ]

    def __str__(self):
        return f"{self.user}'s plan for week of {self.week_start}"
