from django import forms
from .models import FoodItem

class CustomFoodForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        fields = ['name', 'brand', 'serving_size', 'serving_unit', 'calories', 'protein', 'carbohydrates', 'fat']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Homemade Protein Granola'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional brand or source'}),
            'serving_size': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'}),
            'serving_unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., g, ml, cup, piece'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'protein': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'carbohydrates': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'fat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
        }
