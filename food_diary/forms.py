from django import forms
from decimal import Decimal
from .models import FoodEntry

class FoodEntryForm(forms.ModelForm):
    """
    Form for adding and editing a food diary entry.
    Strict server-side validation for food name, positive serving quantities,
    meal categories, and non-negative macronutrient inputs.
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
    quantity = forms.DecimalField(
        required=False,
        initial=Decimal('1.00'),
        min_value=Decimal('0.01'),
        error_messages={
            'min_value': 'Serving quantity must be greater than zero.'
        },
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1', 'value': '1.0'})
    )

    class Meta:
        model = FoodEntry
        fields = [
            'date',
            'meal_category',
            'food_name',
            'brand',
            'quantity',
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
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand, source, or restaurant'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1', 'value': '1.0'}),
            'serving_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'serving_unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'g, ml, piece, cup'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'protein': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'carbohydrates': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'fat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
        }
        error_messages = {
            'food_name': {
                'required': 'Food name is required.'
            }
        }

    def clean_food_name(self):
        name = self.cleaned_data.get('food_name', '').strip()
        if not name:
            raise forms.ValidationError("Food name is required.")
        return name

    def clean_meal_category(self):
        category = self.cleaned_data.get('meal_category')
        valid_cats = ['Breakfast', 'Lunch', 'Dinner', 'Snacks']
        if category not in valid_cats:
            raise forms.ValidationError("Invalid meal category selected.")
        return category

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is None:
            return Decimal('1.00')
        if quantity <= 0:
            raise forms.ValidationError("Serving quantity must be greater than zero.")
        return quantity

    def clean_serving_amount(self):
        amount = self.cleaned_data.get('serving_amount')
        if amount is None or amount <= 0:
            raise forms.ValidationError("Serving amount must be greater than zero.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        calories = cleaned_data.get('calories')
        protein = cleaned_data.get('protein')
        carbs = cleaned_data.get('carbohydrates')
        fat = cleaned_data.get('fat')

        if calories is not None and calories < 0:
            self.add_error('calories', "Calories cannot be negative.")
        if protein is not None and protein < 0:
            self.add_error('protein', "Protein cannot be negative.")
        if carbs is not None and carbs < 0:
            self.add_error('carbohydrates', "Carbohydrates cannot be negative.")
        if fat is not None and fat < 0:
            self.add_error('fat', "Fat cannot be negative.")

        return cleaned_data
