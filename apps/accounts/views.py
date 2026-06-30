"""
Accounts Views - Registration, authentication, profile management.
"""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, UpdateView, ListView, DeleteView, TemplateView

from .forms import (
    CustomerRegistrationForm, EmailLoginForm, UserProfileForm,
    CustomerProfileForm, AddressForm, ForgotPasswordForm, ResetPasswordForm,
)
from .models import Address, CustomerProfile
from .services import AccountService
from .tasks import send_verification_email_task, send_password_reset_email_task


class RegisterView(CreateView):
    """Customer registration with email verification."""
    form_class = CustomerRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:registration_pending')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        # Send verification email asynchronously
        send_verification_email_task.delay(self.object.id)
        messages.success(self.request, 'Account created! Please check your email to verify.')
        return response


class RegistrationPendingView(TemplateView):
    """Page shown after registration, prompting email verification."""
    template_name = 'accounts/registration_pending.html'


class VerifyEmailView(View):
    """Handle email verification token."""
    def get(self, request, token):
        success, message = AccountService.verify_email(token)
        if success:
            messages.success(request, message)
            return redirect('accounts:login')
        else:
            messages.error(request, message)
            return redirect('accounts:login')


class LoginView(View):
    """Email-based login."""
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:home')
        form = EmailLoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_verified:
                messages.warning(request, 'Please verify your email first.')
                return render(request, self.template_name, {'form': form})
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            next_url = request.GET.get('next', 'core:home')
            return redirect(next_url)
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """Logout user."""
    def get(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('core:home')


class ForgotPasswordView(View):
    """Request password reset email."""
    template_name = 'accounts/forgot_password.html'

    def get(self, request):
        form = ForgotPasswordForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            send_password_reset_email_task.delay(form.cleaned_data['email'])
            messages.success(request, 'If an account exists with this email, a reset link has been sent.')
            return redirect('accounts:login')
        return render(request, self.template_name, {'form': form})


class ResetPasswordView(View):
    """Reset password with token."""
    template_name = 'accounts/reset_password.html'

    def get(self, request, token):
        form = ResetPasswordForm()
        return render(request, self.template_name, {'form': form, 'token': token})

    def post(self, request, token):
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            success, message = AccountService.reset_password(token, form.cleaned_data['password1'])
            if success:
                messages.success(request, message)
                return redirect('accounts:login')
            else:
                messages.error(request, message)
        return render(request, self.template_name, {'form': form, 'token': token})


class ProfileView(LoginRequiredMixin, View):
    """User profile management."""
    template_name = 'accounts/profile.html'

    def get(self, request):
        user_form = UserProfileForm(instance=request.user)
        profile_form = None
        if request.user.is_customer:
            profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
            profile_form = CustomerProfileForm(instance=profile)
        return render(request, self.template_name, {
            'user_form': user_form,
            'profile_form': profile_form,
        })

    def post(self, request):
        user_form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        profile_form = None
        if request.user.is_customer:
            profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
            profile_form = CustomerProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and (profile_form is None or profile_form.is_valid()):
            user_form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')

        return render(request, self.template_name, {
            'user_form': user_form,
            'profile_form': profile_form,
        })


class AddressListView(LoginRequiredMixin, ListView):
    """List user's addresses."""
    model = Address
    template_name = 'accounts/addresses.html'
    context_object_name = 'addresses'

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class AddressCreateView(LoginRequiredMixin, CreateView):
    """Add a new address."""
    model = Address
    form_class = AddressForm
    template_name = 'accounts/address_form.html'
    success_url = reverse_lazy('accounts:addresses')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Address added successfully.')
        return super().form_valid(form)


class AddressUpdateView(LoginRequiredMixin, UpdateView):
    """Edit an existing address."""
    model = Address
    form_class = AddressForm
    template_name = 'accounts/address_form.html'
    success_url = reverse_lazy('accounts:addresses')

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Address updated successfully.')
        return super().form_valid(form)


class AddressDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an address."""
    model = Address
    success_url = reverse_lazy('accounts:addresses')

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Address deleted.')
        return super().delete(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Customer dashboard - orders, wishlist overview."""
    template_name = 'accounts/dashboard.html'
