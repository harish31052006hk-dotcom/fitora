from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class FoodItem(models.Model):
    """
    Standard verified foods and user-created custom foods with nutritional values.
    Nutritional numbers are stored based on standard reference serving (e.g., 100g or 1 serving).
    """
    name = models.CharField(max_length=200, db_index=True)
    brand = models.CharField(max_length=150, blank=True, default='')
    serving_size = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('100.00'))
    serving_unit = models.CharField(max_length=50, default='g')
    calories = models.DecimalField(max_digits=7, decimal_places=2, help_text="Calories per reference serving (kcal)")
    protein = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text="Protein in grams")
    carbohydrates = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text="Carbs in grams")
    fat = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text="Fat in grams")
    is_verified = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='custom_foods')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        brand_str = f" ({self.brand})" if self.brand else ""
        return f"{self.name}{brand_str} - {self.calories} kcal / {self.serving_size}{self.serving_unit}"

    def calculate_nutrition(self, amount):
        """
        Calculates exact nutrition based on input amount.
        Formula: (amount / serving_size) * nutrient_value
        Uses Decimal to prevent floating point inaccuracies.
        """
        amount_dec = Decimal(str(amount))
        ratio = amount_dec / self.serving_size
        return {
            'calories': (self.calories * ratio).quantize(Decimal('0.01')),
            'protein': (self.protein * ratio).quantize(Decimal('0.01')),
            'carbohydrates': (self.carbohydrates * ratio).quantize(Decimal('0.01')),
            'fat': (self.fat * ratio).quantize(Decimal('0.01')),
        }
