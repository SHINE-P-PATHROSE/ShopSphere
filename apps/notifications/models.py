"""Notifications Models."""
from django.db import models
from apps.core.models import TimeStampedModel


class Notification(TimeStampedModel):
    TYPE_CHOICES = [
        ('ORDER', 'Order Update'), ('PAYMENT', 'Payment'),
        ('REVIEW', 'Review'), ('PROMO', 'Promotion'),
        ('SYSTEM', 'System'), ('SUPPORT', 'Support'),
    ]

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    link = models.URLField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.user.email}"
