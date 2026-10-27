from django import forms
from .models import Recipe, RecipeIngredient

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
