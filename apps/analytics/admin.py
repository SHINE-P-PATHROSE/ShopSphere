from django.contrib import admin
from .models import DailyAnalytics


@admin.register(DailyAnalytics)
class DailyAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_orders', 'total_revenue', 'new_users', 'conversion_rate']
    date_hierarchy = 'date'
