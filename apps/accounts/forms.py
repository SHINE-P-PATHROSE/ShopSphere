"""
Accounts Forms - Registration, login, profile, and address forms.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.contrib.auth import get_user_model
from .models import CustomerProfile, Address

User = get_user_model()


class CustomerRegistrationForm(UserCreationForm):
    """Registration form for customer users."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 'placeholder': 'Email address',
            'id': 'register-email', 'autocomplete': 'email',
        })
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'First name',
            'id': 'register-first-name',
        })
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Last name',
            'id': 'register-last-name',
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'Password',
            'id': 'register-password',
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'Confirm password',
            'id': 'register-password-confirm',
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'CUSTOMER'
        if commit:
            user.save()
        return user


class EmailLoginForm(AuthenticationForm):
    """Login form using email instead of username."""
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 'placeholder': 'Email address',
            'id': 'login-email', 'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'Password',
            'id': 'login-password',
        })
    )


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'profile-first-name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'profile-last-name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'id': 'profile-phone'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control', 'id': 'profile-avatar'}),
        }


class CustomerProfileForm(forms.ModelForm):
    """Form for customer-specific profile details."""
    class Meta:
        model = CustomerProfile
        fields = ['date_of_birth', 'gender', 'newsletter_subscribed']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date', 'id': 'profile-dob',
            }),
            'gender': forms.Select(attrs={'class': 'form-select', 'id': 'profile-gender'}),
            'newsletter_subscribed': forms.CheckboxInput(attrs={
                'class': 'form-check-input', 'id': 'profile-newsletter',
            }),
        }


class AddressForm(forms.ModelForm):
    """Form for adding/editing addresses."""
    class Meta:
        model = Address
        fields = [
            'full_name', 'phone', 'address_line_1', 'address_line_2',
            'city', 'state', 'postal_code', 'country', 'address_type', 'is_default',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'address-name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'id': 'address-phone'}),
            'address_line_1': forms.TextInput(attrs={'class': 'form-control', 'id': 'address-line1', 'placeholder': 'Street address'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control', 'id': 'address-line2', 'placeholder': 'Apartment, suite, etc.'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'id': 'address-city'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'id': 'address-state'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'id': 'address-postal'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'id': 'address-country'}),
            'address_type': forms.Select(attrs={'class': 'form-select', 'id': 'address-type'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'address-default'}),
        }


class ForgotPasswordForm(forms.Form):
    """Form for requesting a password reset."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 'placeholder': 'Enter your email address',
            'id': 'forgot-email',
        })
    )


class ResetPasswordForm(forms.Form):
    """Form for setting a new password."""
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'New password',
            'id': 'reset-password',
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'Confirm new password',
            'id': 'reset-password-confirm',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords don't match.")
        return cleaned_data
