from django import forms
from .models import SupportTicket

class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'category', 'description', 'contact_email']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief summary of your question or issue'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe what happened, any error message seen, or how we can assist you.'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email address for ticket updates'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            if not self.initial.get('contact_email'):
                self.initial['contact_email'] = user.email
            self.fields['contact_email'].required = False
            self.fields['contact_email'].widget.attrs['placeholder'] = f"Using {user.email}"
        else:
            self.fields['contact_email'].required = True

    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '').strip()
        if not subject or len(subject) < 3:
            raise forms.ValidationError("Subject must be at least 3 characters long.")
        return subject

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if not description or len(description) < 5:
            raise forms.ValidationError("Please provide a more detailed description (at least 5 characters).")
        return description
