from decimal import Decimal
from django import forms
from django.utils import timezone
from .models import WeightLog

class WeightLogForm(forms.ModelForm):
    class Meta:
        model = WeightLog
        fields = ['date', 'weight', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '20', 'max': '400', 'placeholder': 'e.g., 74.5'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Fasted morning weigh-in'}),
        }
        error_messages = {
            'date': {'required': 'Measurement date is required.'},
            'weight': {'required': 'Weight measurement is required.'}
        }

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is None:
            raise forms.ValidationError("Weight measurement is required.")
        if weight <= Decimal('20.00') or weight > Decimal('500.00'):
            raise forms.ValidationError("Please enter a valid weight between 20.0 kg and 500.0 kg.")
        return weight

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if not date:
            raise forms.ValidationError("Measurement date is required.")
        today = timezone.now().date()
        if date > today:
            raise forms.ValidationError("Measurement date cannot be in the future.")
        return date
