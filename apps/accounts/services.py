"""
Accounts Services - Business logic for user management.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import User, EmailVerificationToken, PasswordResetToken

logger = logging.getLogger(__name__)


class AccountService:
    """Service layer for account operations."""

    @staticmethod
    def send_verification_email(user):
        """Send email verification link to user."""
        token, _ = EmailVerificationToken.objects.get_or_create(user=user)
        verification_url = f"{settings.SITE_URL}/accounts/verify-email/{token.token}/"

        subject = f"Verify your {settings.SITE_NAME} account"
        html_message = render_to_string('accounts/emails/verify_email.html', {
            'user': user,
            'verification_url': verification_url,
            'site_name': settings.SITE_NAME,
        })
        plain_message = strip_tags(html_message)

        try:
            send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL,
                      [user.email], html_message=html_message)
            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {e}")

    @staticmethod
    def verify_email(token_uuid):
        """Verify user's email with the given token."""
        try:
            token = EmailVerificationToken.objects.get(token=token_uuid)
            if token.is_valid():
                token.user.is_verified = True
                token.user.save(update_fields=['is_verified'])
                token.delete()
                return True, "Email verified successfully."
            else:
                token.delete()
                return False, "Verification link has expired."
        except EmailVerificationToken.DoesNotExist:
            return False, "Invalid verification link."

    @staticmethod
    def send_password_reset_email(email):
        """Send password reset email."""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return  # Don't reveal if email exists

        token = PasswordResetToken.objects.create(user=user)
        reset_url = f"{settings.SITE_URL}/accounts/reset-password/{token.token}/"

        subject = f"Reset your {settings.SITE_NAME} password"
        html_message = render_to_string('accounts/emails/password_reset.html', {
            'user': user,
            'reset_url': reset_url,
            'site_name': settings.SITE_NAME,
        })
        plain_message = strip_tags(html_message)

        try:
            send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL,
                      [user.email], html_message=html_message)
            logger.info(f"Password reset email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")

    @staticmethod
    def reset_password(token_uuid, new_password):
        """Reset user password with the given token."""
        try:
            token = PasswordResetToken.objects.get(token=token_uuid)
            if token.is_valid():
                token.user.set_password(new_password)
                token.user.save()
                token.used = True
                token.save(update_fields=['used'])
                return True, "Password reset successfully."
            else:
                return False, "Reset link has expired."
        except PasswordResetToken.DoesNotExist:
            return False, "Invalid reset link."
