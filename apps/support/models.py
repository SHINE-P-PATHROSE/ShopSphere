"""Support Models."""
from django.db import models
from apps.core.models import TimeStampedModel


class SupportTicket(TimeStampedModel):
    STATUS_CHOICES = [('OPEN','Open'),('IN_PROGRESS','In Progress'),('RESOLVED','Resolved'),('CLOSED','Closed')]
    PRIORITY_CHOICES = [('LOW','Low'),('MEDIUM','Medium'),('HIGH','High'),('URGENT','Urgent')]
    CATEGORY_CHOICES = [('ORDER','Order'),('PAYMENT','Payment'),('PRODUCT','Product'),('ACCOUNT','Account'),('OTHER','Other')]

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=200)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='OPEN', db_index=True)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    assigned_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')

    def __str__(self):
        return f"#{self.id} - {self.subject}"


class TicketMessage(TimeStampedModel):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    body = models.TextField()
    attachment = models.FileField(upload_to='support/attachments/', blank=True)
    is_staff_reply = models.BooleanField(default=False)
