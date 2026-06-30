from django.contrib import admin
from .models import SupportTicket, TicketMessage


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'user', 'category', 'priority', 'status']
    list_filter = ['status', 'priority', 'category']
    inlines = [TicketMessageInline]
