from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Recipe(models.Model):
    """
    User-created recipe or saved custom meal with ingredient breakdown and serving calculations.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    servings = models.PositiveIntegerField(default=1, help_text="Number of servings produced by this recipe")
    is_favorite_meal = models.BooleanField(default=False, help_text="Mark as a quick-add favorite meal")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.servings} servings) by {self.user.username}"

    @property
    def total_calories(self):
        return sum((ing.calories for ing in self.ingredients.all()), Decimal('0.00'))

    @property
    def total_protein(self):
        return sum((ing.protein for ing in self.ingredients.all()), Decimal('0.00'))

    @property
    def total_carbohydrates(self):
        return sum((ing.carbohydrates for ing in self.ingredients.all()), Decimal('0.00'))

    @property
    def total_fat(self):
        return sum((ing.fat for ing in self.ingredients.all()), Decimal('0.00'))

    @property
    def per_serving_calories(self):
        s = Decimal(str(max(1, self.servings)))
        return (self.total_calories / s).quantize(Decimal('0.01'))

    @property
    def per_serving_protein(self):
        s = Decimal(str(max(1, self.servings)))
        return (self.total_protein / s).quantize(Decimal('0.01'))

    @property
    def per_serving_carbohydrates(self):
        s = Decimal(str(max(1, self.servings)))
        return (self.total_carbohydrates / s).quantize(Decimal('0.01'))

    @property
    def per_serving_fat(self):
        s = Decimal(str(max(1, self.servings)))
        return (self.total_fat / s).quantize(Decimal('0.01'))


class RecipeIngredient(models.Model):
    """
    Individual ingredient in a recipe with calculated nutritional values.
    """
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    food_name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=7, decimal_places=2, help_text="Quantity of ingredient")
    unit = models.CharField(max_length=50, default='g')
    calories = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'))
    protein = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    carbohydrates = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    fat = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.amount}{self.unit} {self.food_name} ({self.calories} kcal)"
