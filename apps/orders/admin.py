from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, ReturnRequest, Refund


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['variant', 'store', 'quantity', 'price', 'total']


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['status', 'changed_by', 'notes', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['order_number', 'user__email', 'guest_email']
    readonly_fields = ['order_number']
    inlines = [OrderItemInline, OrderStatusHistoryInline]


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ['order_item', 'reason', 'status', 'created_at']
    list_filter = ['status']
    actions = ['approve_returns', 'reject_returns']

    @admin.action(description='Approve returns')
    def approve_returns(self, request, queryset):
        queryset.update(status='APPROVED')

    @admin.action(description='Reject returns')
    def reject_returns(self, request, queryset):
        queryset.update(status='REJECTED')
