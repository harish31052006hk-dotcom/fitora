from django import forms
from decimal import Decimal
from .models import FoodEntry

class FoodEntryForm(forms.ModelForm):
    """
    Form for adding and editing a food diary entry.
    Validates serving amounts and nutritional values.
    """
    base_serving_size = forms.DecimalField(
        required=False,
        initial=Decimal('100.00'),
        widget=forms.HiddenInput()
    )
    base_calories = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput()
    )
    base_protein = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput()
    )
    base_carbohydrates = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput()
    )
    base_fat = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = FoodEntry
        fields = [
            'date',
            'meal_category',
            'food_name',
            'brand',
            'serving_amount',
            'serving_unit',
            'calories',
            'protein',
            'carbohydrates',
            'fat'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'meal_category': forms.Select(attrs={'class': 'form-select'}),
            'food_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Grilled Chicken Breast'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand or restaurant (optional)'}),
            'serving_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'serving_unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'g, ml, serving'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'protein': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'carbohydrates': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'fat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        serving_amount = cleaned_data.get('serving_amount')
        calories = cleaned_data.get('calories')

        if serving_amount is not None and serving_amount <= 0:
            self.add_error('serving_amount', "Serving amount must be greater than zero.")

        if calories is not None and calories < 0:
            self.add_error('calories', "Calories cannot be negative.")

        return cleaned_data
