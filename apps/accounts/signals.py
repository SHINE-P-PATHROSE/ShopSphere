"""
Accounts Signals - Auto-create profiles on user creation.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, CustomerProfile


@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    """Automatically create a customer profile for new customer users."""
    if created and instance.role == 'CUSTOMER':
        CustomerProfile.objects.get_or_create(user=instance)
