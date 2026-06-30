from django.urls import path
from .api_views import NotificationListAPIView, MarkReadAPIView

urlpatterns = [
    path('', NotificationListAPIView.as_view(), name='api-notifications'),
    path('<int:pk>/read/', MarkReadAPIView.as_view(), name='api-notification-read'),
    path('read-all/', MarkReadAPIView.as_view(), name='api-notifications-read-all'),
]
