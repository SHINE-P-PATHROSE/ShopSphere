"""Analytics Celery tasks."""
from celery import shared_task

from .services import AnalyticsService


@shared_task
def generate_daily_report():
    AnalyticsService.generate_daily_report()
    return 'Daily analytics report generated'
