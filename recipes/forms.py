from django import forms
from .models import Recipe, RecipeIngredient, SavedMeal, SavedMealItem

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['name', 'description', 'servings', 'is_favorite_meal']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Post-Workout High Protein Bowl'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional prep notes, instructions or description'}),
            'servings': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 50}),
            'is_favorite_meal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class RecipeIngredientForm(forms.ModelForm):
    class Meta:
        model = RecipeIngredient
        fields = ['food_name', 'amount', 'unit', 'calories', 'protein', 'carbohydrates', 'fat']
        widgets = {
            'food_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingredient name (e.g., Chicken Breast)'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'g, ml, cup'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'protein': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'carbohydrates': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'fat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
        }

class SavedMealForm(forms.ModelForm):
    class Meta:
        model = SavedMeal
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Quick Power Breakfast'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional meal notes or context'}),
        }

class SavedMealItemForm(forms.ModelForm):
    class Meta:
        model = SavedMealItem
        fields = ['food_name', 'quantity', 'serving_unit', 'calories', 'protein', 'carbohydrates', 'fat']
        widgets = {
            'food_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Food name (e.g., 2 Boiled Eggs)'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1', 'value': '1.0'}),
            'serving_unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'serving, portion, g'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'protein': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'carbohydrates': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'fat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
        }
