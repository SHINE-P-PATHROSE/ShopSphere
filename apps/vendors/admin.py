from django.contrib import admin
from .models import VendorProfile, Store, StorePolicy


class StorePolicyInline(admin.TabularInline):
    model = StorePolicy
    extra = 0


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user', 'status', 'commission_rate', 'created_at']
    list_filter = ['status']
    search_fields = ['business_name', 'user__email']
    actions = ['approve_vendors', 'reject_vendors']

    @admin.action(description='Approve selected vendors')
    def approve_vendors(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='APPROVED', approved_at=timezone.now())

    @admin.action(description='Reject selected vendors')
    def reject_vendors(self, request, queryset):
        queryset.update(status='REJECTED')


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'is_active', 'total_sales']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [StorePolicyInline]
