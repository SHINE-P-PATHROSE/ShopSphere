"""
Accounts API tests — registration, email verification, login, and profile.
"""
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import EmailVerificationToken

User = get_user_model()


@pytest.mark.django_db
class TestRegistration:
    """POST /api/v1/auth/register/"""

    def test_register_creates_unverified_user(self, api_client):
        response = api_client.post('/api/v1/auth/register/', {
            'email': 'newuser@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
        })
        assert response.status_code == 201
        user = User.objects.get(email='newuser@test.com')
        assert user.is_verified is False
        assert user.role == 'CUSTOMER'

    def test_register_returns_verification_message(self, api_client):
        response = api_client.post('/api/v1/auth/register/', {
            'email': 'another@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Another',
            'last_name': 'User',
        })
        assert response.status_code == 201
        assert 'verify your account' in response.data['detail'].lower()

    def test_register_password_mismatch_returns_400(self, api_client):
        response = api_client.post('/api/v1/auth/register/', {
            'email': 'mismatch@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'WrongPass123!',
            'first_name': 'X',
            'last_name': 'Y',
        })
        assert response.status_code == 400

    def test_register_duplicate_email_returns_400(self, api_client, customer_user):
        response = api_client.post('/api/v1/auth/register/', {
            'email': customer_user.email,
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Dup',
            'last_name': 'User',
        })
        assert response.status_code == 400


@pytest.mark.django_db
class TestEmailVerification:
    """POST /api/v1/auth/verify-email/ and /resend-verification/"""

    def test_verify_email_with_valid_token(self, api_client, unverified_user):
        token = EmailVerificationToken.objects.create(user=unverified_user)
        response = api_client.post('/api/v1/auth/verify-email/', {'token': str(token.token)})
        assert response.status_code == 200
        unverified_user.refresh_from_db()
        assert unverified_user.is_verified is True

    def test_verify_email_with_invalid_token_returns_400(self, api_client):
        import uuid
        response = api_client.post('/api/v1/auth/verify-email/', {'token': str(uuid.uuid4())})
        assert response.status_code == 400

    def test_resend_verification_for_existing_unverified_user(self, api_client, unverified_user):
        response = api_client.post('/api/v1/auth/resend-verification/', {'email': unverified_user.email})
        assert response.status_code == 200

    def test_resend_verification_for_nonexistent_email_still_returns_200(self, api_client):
        """Never reveal whether an email exists."""
        response = api_client.post('/api/v1/auth/resend-verification/', {'email': 'ghost@example.com'})
        assert response.status_code == 200


@pytest.mark.django_db
class TestLogin:
    """POST /api/v1/auth/login/"""

    def test_verified_user_gets_tokens(self, api_client, customer_user):
        response = api_client.post('/api/v1/auth/login/', {
            'email': customer_user.email,
            'password': 'TestPass123!',
        })
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_unverified_user_is_blocked(self, api_client, unverified_user):
        response = api_client.post('/api/v1/auth/login/', {
            'email': unverified_user.email,
            'password': 'TestPass123!',
        })
        assert response.status_code == 401
        # Custom exception handler wraps errors under response.data['error']['details']
        error_detail = str(response.data['error']['details']['detail']).lower()
        assert 'not verified' in error_detail

    def test_wrong_password_returns_401(self, api_client, customer_user):
        response = api_client.post('/api/v1/auth/login/', {
            'email': customer_user.email,
            'password': 'WrongPassword!',
        })
        assert response.status_code == 401


@pytest.mark.django_db
class TestProfile:
    """GET/PATCH /api/v1/auth/profile/"""

    def test_authenticated_user_can_get_profile(self, auth_client, customer_user):
        response = auth_client.get('/api/v1/auth/profile/')
        assert response.status_code == 200
        assert response.data['email'] == customer_user.email
        assert response.data['is_verified'] is True

    def test_unauthenticated_request_returns_401(self, api_client):
        response = api_client.get('/api/v1/auth/profile/')
        assert response.status_code == 401

    def test_authenticated_user_can_update_name(self, auth_client, customer_user):
        response = auth_client.patch('/api/v1/auth/profile/', {'first_name': 'Updated'})
        assert response.status_code == 200
        customer_user.refresh_from_db()
        assert customer_user.first_name == 'Updated'
