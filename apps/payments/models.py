"""Payments Models - Payment transactions and webhook logs."""
from django.db import models
from apps.core.models import TimeStampedModel


class Payment(TimeStampedModel):
    GATEWAY_CHOICES = [('STRIPE', 'Stripe'), ('RAZORPAY', 'Razorpay'), ('COD', 'Cash on Delivery')]
    STATUS_CHOICES = [('PENDING', 'Pending'), ('SUCCESS', 'Success'), ('FAILED', 'Failed'), ('REFUNDED', 'Refunded')]

    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='payment')
    gateway = models.CharField(max_length=10, choices=GATEWAY_CHOICES)
    transaction_id = models.CharField(max_length=200, blank=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    gateway_response = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"


class WebhookLog(TimeStampedModel):
    gateway = models.CharField(max_length=10)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    error = models.TextField(blank=True)
