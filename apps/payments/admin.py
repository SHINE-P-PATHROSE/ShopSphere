from django.contrib import admin
from .models import Payment, WebhookLog


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'gateway', 'amount', 'status', 'transaction_id', 'paid_at']
    list_filter = ['gateway', 'status']


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ['gateway', 'event_type', 'processed', 'created_at']
    readonly_fields = ['payload']
