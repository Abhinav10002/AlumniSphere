from django import forms
from django.contrib.auth.models import User
from .models import Profile

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'headline', 'bio', 'graduation_year', 'company', 'location']
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'headline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Full-Stack Developer at Acme Corp'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about your career journey...'}),
            'graduation_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2024'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Google / Microsoft'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. New York, NY'}),
        }