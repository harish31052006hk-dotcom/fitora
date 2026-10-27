from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class WeightLog(models.Model):
    """
    User weight tracking history over time.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_logs')
    date = models.DateField(default=timezone.now, db_index=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kilograms (kg)")
    notes = models.CharField(max_length=255, blank=True, default='', help_text="Optional reflection or context")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username}: {self.weight} kg on {self.date}"
