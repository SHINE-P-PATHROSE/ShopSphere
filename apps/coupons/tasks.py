"""Coupon Celery tasks."""
from celery import shared_task
from django.utils import timezone

from .models import Coupon


@shared_task
def expire_coupons():
    updated = Coupon.objects.filter(is_active=True, valid_to__lt=timezone.now()).update(
        is_active=False
    )
    return f'Expired {updated} coupons'
