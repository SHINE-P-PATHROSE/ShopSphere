"""Product Celery tasks."""
from celery import shared_task
from django.db import models

from .models import ProductVariant


@shared_task
def check_low_stock_alerts():
    low_stock = ProductVariant.objects.filter(
        is_active=True, stock__lte=models.F('low_stock_threshold'), stock__gt=0
    )
    count = low_stock.count()
    return f'{count} variants below low stock threshold'
