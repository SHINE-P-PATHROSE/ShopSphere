from django.urls import path
from .api_views import AdminAnalyticsAPIView, VendorAnalyticsAPIView

urlpatterns = [
    path('admin/', AdminAnalyticsAPIView.as_view(), name='api-analytics-admin'),
    path('vendor/', VendorAnalyticsAPIView.as_view(), name='api-analytics-vendor'),
]
