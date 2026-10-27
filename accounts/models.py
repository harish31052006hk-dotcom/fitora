from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    """
    User profile storing personalized nutrition goals and metrics.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    daily_calorie_goal = models.PositiveIntegerField(
        default=2000,
        help_text="Target daily energy intake in kilocalories (kcal)"
    )
    daily_protein_goal = models.PositiveIntegerField(
        default=140,
        help_text="Target daily protein in grams (g)"
    )
    daily_carbs_goal = models.PositiveIntegerField(
        default=220,
        help_text="Target daily carbohydrates in grams (g)"
    )
    daily_fat_goal = models.PositiveIntegerField(
        default=65,
        help_text="Target daily fat in grams (g)"
    )
    current_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Current body weight in kg"
    )
    target_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Goal body weight in kg"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.daily_calorie_goal} kcal)"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # Save profile if it exists
        if hasattr(instance, 'profile'):
            instance.profile.save()
