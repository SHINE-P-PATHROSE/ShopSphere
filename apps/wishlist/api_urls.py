"""Wishlist URLs."""
from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.WishlistListAPIView.as_view(), name='api-wishlist'),
    path('toggle/', api_views.WishlistToggleAPIView.as_view(), name='api-wishlist-toggle'),
]
