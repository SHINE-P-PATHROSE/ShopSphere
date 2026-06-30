"""
Core Context Processors - Global template context.
"""
from django.conf import settings


def site_settings(request):
    """Inject site-wide settings into all templates."""
    return {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_URL': settings.SITE_URL,
        'DEBUG': settings.DEBUG,
    }
