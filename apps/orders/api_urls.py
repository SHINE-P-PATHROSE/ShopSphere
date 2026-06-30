"""Order API URLs."""
from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.OrderListAPIView.as_view(), name='api-orders'),
    path('checkout/', api_views.CheckoutAPIView.as_view(), name='api-checkout'),
    path('<str:order_number>/', api_views.OrderDetailAPIView.as_view(), name='api-order-detail'),
    path('returns/', api_views.ReturnRequestCreateAPIView.as_view(), name='api-returns'),
]
