from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegisterForm(UserCreationForm):
    """
    Custom user registration form that uses email as the primary identifier
    """
    name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Full Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address'})
    )
    country = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Country'})
    )

    class Meta:
        model = User
        fields = ['email', 'name', 'country', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)

        
        name_parts = self.cleaned_data.get('name', '').strip().split(' ', 1)
        user.first_name = name_parts[0] if len(name_parts) > 0 else ''
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''

        user.email = self.cleaned_data['email']
        user.country = self.cleaned_data.get('country', '')

        
        user.is_active = False

        if commit:
            user.save()
        return user
