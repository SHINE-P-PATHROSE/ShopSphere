"""
Core Permissions - Custom DRF permissions for role-based access.
"""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Only allow admin users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'


class IsVendor(BasePermission):
    """Only allow approved vendor users."""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'VENDOR' and
            hasattr(request.user, 'vendor_profile') and
            request.user.vendor_profile.status == 'APPROVED'
        )


class IsCustomer(BasePermission):
    """Only allow customer users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'CUSTOMER'


class IsVendorOrAdmin(BasePermission):
    """Allow vendor or admin users."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['VENDOR', 'ADMIN']


class IsOwnerOrAdmin(BasePermission):
    """Allow object owner or admin."""
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN':
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'vendor'):
            return obj.vendor.user == request.user
        return False
