"""Analytics service layer."""
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Count, Sum
from django.utils import timezone

from apps.orders.models import Order, OrderItem
from apps.accounts.models import User
from apps.vendors.models import VendorProfile
from apps.products.models import Product
from .models import DailyAnalytics


class AnalyticsService:
    """Platform, vendor, and customer analytics."""

    @staticmethod
    def admin_dashboard(days=30):
        since = timezone.now() - timedelta(days=days)
        orders = Order.objects.filter(created_at__gte=since).exclude(status='CANCELLED')
        revenue = orders.aggregate(total=Sum('total'))['total'] or Decimal('0')
        order_count = orders.count()
        return {
            'total_revenue': revenue,
            'total_orders': order_count,
            'avg_order_value': (revenue / order_count) if order_count else Decimal('0'),
            'new_customers': User.objects.filter(role='CUSTOMER', date_joined__gte=since).count(),
            'new_vendors': VendorProfile.objects.filter(created_at__gte=since).count(),
            'pending_vendors': VendorProfile.objects.filter(status='PENDING').count(),
            'top_products': Product.objects.filter(status='APPROVED').order_by('-sales_count')[:10],
            'orders_by_status': list(
                orders.values('status').annotate(count=Count('id')).order_by('-count')
            ),
            'revenue_trend': AnalyticsService._revenue_trend(days),
        }

    @staticmethod
    def vendor_dashboard(store, days=30):
        since = timezone.now() - timedelta(days=days)
        items = OrderItem.objects.filter(
            store=store, created_at__gte=since
        ).exclude(order__status='CANCELLED')
        revenue = items.aggregate(total=Sum('total'))['total'] or Decimal('0')
        return {
            'total_sales': items.count(),
            'total_revenue': revenue,
            'top_products': items.values(
                'variant__product__title'
            ).annotate(qty=Sum('quantity'), rev=Sum('total')).order_by('-rev')[:5],
            'recent_orders': items.select_related('order').order_by('-created_at')[:10],
        }

    @staticmethod
    def _revenue_trend(days=30):
        since = timezone.now().date() - timedelta(days=days)
        return list(
            DailyAnalytics.objects.filter(date__gte=since).values(
                'date', 'total_revenue', 'total_orders'
            ).order_by('date')
        )

    @staticmethod
    def generate_daily_report(date=None):
        date = date or (timezone.now().date() - timedelta(days=1))
        start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end = start + timedelta(days=1)

        orders = Order.objects.filter(created_at__gte=start, created_at__lt=end).exclude(
            status='CANCELLED'
        )
        revenue = orders.aggregate(total=Sum('total'))['total'] or Decimal('0')
        count = orders.count()

        DailyAnalytics.objects.update_or_create(
            date=date,
            defaults={
                'total_orders': count,
                'total_revenue': revenue,
                'new_users': User.objects.filter(date_joined__gte=start, date_joined__lt=end).count(),
                'new_vendors': VendorProfile.objects.filter(
                    created_at__gte=start, created_at__lt=end
                ).count(),
                'avg_order_value': (revenue / count) if count else Decimal('0'),
            },
        )
