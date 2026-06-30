"""Analytics models and reporting."""
from django.db import models
from apps.core.models import TimeStampedModel


class DailyAnalytics(TimeStampedModel):
    """Aggregated daily platform metrics."""
    date = models.DateField(unique=True, db_index=True)
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    new_users = models.PositiveIntegerField(default=0)
    new_vendors = models.PositiveIntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name_plural = 'Daily Analytics'
        ordering = ['-date']

    def __str__(self):
        return f"Analytics {self.date}"
