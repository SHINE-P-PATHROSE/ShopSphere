"""
Global pytest fixtures for ShopSphere.
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def customer_user(db):
    return User.objects.create_user(
        email='customer@example.com',
        password='TestPass123!',
        first_name='Test',
        last_name='Customer',
        role='CUSTOMER',
        is_verified=True,
    )


@pytest.fixture
def unverified_user(db):
    """A customer who has not yet verified their email."""
    return User.objects.create_user(
        email='unverified@example.com',
        password='TestPass123!',
        first_name='Unverified',
        last_name='User',
        role='CUSTOMER',
        is_verified=False,
    )


@pytest.fixture
def vendor_user(db):
    user = User.objects.create_user(
        email='vendor@example.com',
        password='TestPass123!',
        first_name='Test',
        last_name='Vendor',
        role='VENDOR',
        is_verified=True,
    )
    VendorProfile.objects.create(
        user=user,
        business_name='Test Store',
        business_email='vendor@example.com',
        business_phone='9999999999',
        status='APPROVED',
    )
    # Store is auto-created by the create_store_on_approval signal
    return user


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email='admin@example.com',
        password='AdminPass123!',
        first_name='Admin',
        last_name='User',
        role='ADMIN',
        is_verified=True,
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def auth_client(api_client, customer_user):
    """API client authenticated as a verified customer."""
    api_client.force_authenticate(user=customer_user)
    return api_client


@pytest.fixture
def vendor_client(api_client, vendor_user):
    """API client authenticated as an approved vendor."""
    api_client.force_authenticate(user=vendor_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """API client authenticated as an admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client
