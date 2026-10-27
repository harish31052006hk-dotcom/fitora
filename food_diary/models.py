from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class FoodEntry(models.Model):
    """
    Individual food entry in a user's daily diary.
    Calculated via: entry nutrition = nutrition per serving × quantity
    Uses Decimal fields to prevent floating point inaccuracies.
    """
    MEAL_BREAKFAST = 'Breakfast'
    MEAL_LUNCH = 'Lunch'
    MEAL_DINNER = 'Dinner'
    MEAL_SNACKS = 'Snacks'

    MEAL_CHOICES = [
        (MEAL_BREAKFAST, 'Breakfast'),
        (MEAL_LUNCH, 'Lunch'),
        (MEAL_DINNER, 'Dinner'),
        (MEAL_SNACKS, 'Snacks'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_entries')
    food_item = models.ForeignKey(
        'nutrition.FoodItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diary_entries',
        help_text="Underlying FoodItem from database if selected"
    )
    date = models.DateField(default=timezone.now, db_index=True)
    meal_category = models.CharField(max_length=20, choices=MEAL_CHOICES, db_index=True)
    food_name = models.CharField(max_length=200)
    brand = models.CharField(max_length=150, blank=True, default='')
    serving_description = models.CharField(max_length=150, blank=True, default='')
    quantity = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Number of servings or portions consumed"
    )
    serving_amount = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal('100.00'),
        help_text="Consumed amount in unit measure (e.g., 150g)"
    )
    serving_unit = models.CharField(max_length=50, default='g')
    calories = models.DecimalField(max_digits=8, decimal_places=2, help_text="Total calories consumed (kcal)")
    protein = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'), help_text="Total protein consumed in grams")
    carbohydrates = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'), help_text="Total carbohydrates consumed in grams")
    fat = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'), help_text="Total fat consumed in grams")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'created_at']
        verbose_name_plural = 'Food entries'

    def __str__(self):
        return f"{self.user.username} - {self.meal_category}: {self.food_name} ({self.calories} kcal)"
