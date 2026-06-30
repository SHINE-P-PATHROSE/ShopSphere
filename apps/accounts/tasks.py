"""
Accounts Celery Tasks - Async email operations.
"""
from celery import shared_task
from .services import AccountService


@shared_task(name='accounts.send_verification_email')
def send_verification_email_task(user_id):
    from .models import User
    try:
        user = User.objects.get(id=user_id)
        AccountService.send_verification_email(user)
    except User.DoesNotExist:
        pass


@shared_task(name='accounts.send_password_reset_email')
def send_password_reset_email_task(email):
    AccountService.send_password_reset_email(email)
