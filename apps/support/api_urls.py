from django.urls import path
from .api_views import TicketListCreateAPIView, TicketDetailAPIView

urlpatterns = [
    path('', TicketListCreateAPIView.as_view(), name='api-tickets'),
    path('<int:pk>/', TicketDetailAPIView.as_view(), name='api-ticket-detail'),
]
