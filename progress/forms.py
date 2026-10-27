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
