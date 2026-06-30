from django.urls import path
from .api_views import CouponValidateAPIView

urlpatterns = [
    path('validate/', CouponValidateAPIView.as_view(), name='api-coupon-validate'),
]
