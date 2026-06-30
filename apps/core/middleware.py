"""
Core Middleware - Audit logging and request tracking.
"""
import json
import logging

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class AuditLogMiddleware(MiddlewareMixin):
    """Middleware to track user activity for audit purposes."""

    AUDIT_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    EXCLUDED_PATHS = ['/static/', '/media/', '/api/schema/', '/__debug__/']

    def process_request(self, request):
        """Store request metadata for potential audit logging."""
        if request.method in self.AUDIT_METHODS:
            request._audit_ip = self.get_client_ip(request)
            request._audit_user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
