"""Cart Celery tasks."""
from celery import shared_task
from datetime import timedelta
from django.utils import timezone

from .models import Cart


@shared_task
def cleanup_abandoned_carts():
    """Remove guest carts older than 30 days."""
    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = Cart.objects.filter(
        user__isnull=True, updated_at__lt=cutoff
    ).delete()
    return f'Deleted {deleted} abandoned carts'
