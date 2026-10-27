from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )
    first_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'daily_calorie_goal',
            'daily_protein_goal',
            'daily_carbs_goal',
            'daily_fat_goal',
            'current_weight',
            'target_weight'
        ]
        widgets = {
            'daily_calorie_goal': forms.NumberInput(attrs={'class': 'form-control', 'min': 500, 'max': 10000}),
            'daily_protein_goal': forms.NumberInput(attrs={'class': 'form-control', 'min': 10, 'max': 600}),
            'daily_carbs_goal': forms.NumberInput(attrs={'class': 'form-control', 'min': 10, 'max': 1000}),
            'daily_fat_goal': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 500}),
            'current_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': 20, 'max': 400}),
            'target_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': 20, 'max': 400}),
        }
