from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import api_views

urlpatterns = [
    # Registration & email verification
    path('register/', api_views.RegisterAPIView.as_view(), name='api_register'),
    path('verify-email/', api_views.VerifyEmailAPIView.as_view(), name='api_verify_email'),
    path('resend-verification/', api_views.ResendVerificationEmailAPIView.as_view(), name='api_resend_verification'),

    # JWT authentication — uses the verified-guard wrapper
    path('login/', api_views.VerifiedTokenObtainPairView.as_view(), name='api_token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),

    # Profile & addresses
    path('profile/', api_views.ProfileAPIView.as_view(), name='api_profile'),
    path('addresses/', api_views.AddressListCreateAPIView.as_view(), name='api_addresses'),
    path('addresses/<int:pk>/', api_views.AddressDetailAPIView.as_view(), name='api_address_detail'),
]
