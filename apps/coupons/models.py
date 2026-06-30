"""Coupons Models."""
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


class Coupon(TimeStampedModel):
    DISCOUNT_TYPES = [('PERCENTAGE', 'Percentage'), ('FIXED', 'Fixed Amount')]

    code = models.CharField(max_length=20, unique=True, db_index=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    per_user_limit = models.PositiveIntegerField(default=1)
    times_used = models.PositiveIntegerField(default=0)
    vendor = models.ForeignKey('vendors.Store', on_delete=models.CASCADE, null=True, blank=True, related_name='coupons')
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} ({self.discount_value}{'%' if self.discount_type == 'PERCENTAGE' else '₹'})"

    @property
    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_to and (self.usage_limit is None or self.times_used < self.usage_limit)


class CouponUsage(TimeStampedModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ['coupon', 'order']
