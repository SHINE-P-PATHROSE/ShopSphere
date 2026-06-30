"""
Celery configuration for ShopSphere.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('shopsphere')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Scheduled tasks
app.conf.beat_schedule = {
    'check-low-stock': {
        'task': 'apps.products.tasks.check_low_stock_alerts',
        'schedule': crontab(hour='*/6'),
    },
    'expire-coupons': {
        'task': 'apps.coupons.tasks.expire_coupons',
        'schedule': crontab(hour=0, minute=0),
    },
    'generate-daily-analytics': {
        'task': 'apps.analytics.tasks.generate_daily_report',
        'schedule': crontab(hour=1, minute=0),
    },
    'cleanup-abandoned-carts': {
        'task': 'apps.cart.tasks.cleanup_abandoned_carts',
        'schedule': crontab(hour=3, minute=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
