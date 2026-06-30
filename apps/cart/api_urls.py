"""Cart API URLs."""
from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.CartAPIView.as_view(), name='api-cart'),
    path('items/<int:pk>/', api_views.CartItemDetailAPIView.as_view(), name='api-cart-item'),
]
