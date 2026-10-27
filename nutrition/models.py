from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class FoodItem(models.Model):
    """
    Standard starter food items and user-created custom foods with nutritional values.
    Nutritional values represent estimated nutrition per reference serving.
    """
    name = models.CharField(max_length=200, db_index=True)
    brand = models.CharField(max_length=150, blank=True, default='')
    serving_description = models.CharField(
        max_length=150,
        blank=True,
        default='100g',
        help_text="Standard portion description (e.g., '1 piece (40g)', '1 cup (240ml)', '100g')"
    )
    serving_size = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('100.00'))
    serving_unit = models.CharField(max_length=50, default='g')
    calories = models.DecimalField(max_digits=7, decimal_places=2, help_text="Estimated calories per reference serving (kcal)")
    protein = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text="Protein in grams")
    carbohydrates = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text="Carbohydrates in grams")
    fat = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text="Fat in grams")
    data_source = models.CharField(
        max_length=150,
        default='Fitora Verified Database (Estimated)',
        help_text="Origin of the nutritional estimate"
    )
    is_verified = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='custom_foods')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    @property
    def calories_per_serving(self):
        return self.calories

    @property
    def protein_per_serving(self):
        return self.protein

    @property
    def carbs_per_serving(self):
        return self.carbohydrates

    @property
    def fat_per_serving(self):
        return self.fat

    def __str__(self):
        brand_str = f" ({self.brand})" if self.brand else ""
        desc_str = f" [{self.serving_description}]" if self.serving_description else f" - {self.serving_size}{self.serving_unit}"
        return f"{self.name}{brand_str}{desc_str} - {self.calories} kcal"

    def calculate_nutrition(self, quantity_or_amount):
        """
        Calculates exact nutrition based on input quantity or amount.
        Formula: (quantity_or_amount / serving_size) * nutrient_value
        Uses Decimal to prevent floating point inaccuracies.
        """
        amount_dec = Decimal(str(quantity_or_amount))
        ratio = amount_dec / self.serving_size if self.serving_size > 0 else Decimal('1.00')
        return {
            'calories': (self.calories * ratio).quantize(Decimal('0.01')),
            'protein': (self.protein * ratio).quantize(Decimal('0.01')),
            'carbohydrates': (self.carbohydrates * ratio).quantize(Decimal('0.01')),
            'fat': (self.fat * ratio).quantize(Decimal('0.01')),
        }
