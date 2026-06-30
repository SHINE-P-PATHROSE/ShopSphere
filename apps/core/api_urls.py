"""
Core API URL Configuration - Aggregates all app API routes under /api/v1/.
"""
from django.urls import include, path

urlpatterns = [
    path('auth/', include('apps.accounts.api_urls')),
    path('products/', include('apps.products.api_urls')),
    path('cart/', include('apps.cart.api_urls')),
    path('wishlist/', include('apps.wishlist.api_urls')),
    path('orders/', include('apps.orders.api_urls')),
    path('reviews/', include('apps.reviews.api_urls')),
    path('vendors/', include('apps.vendors.api_urls')),
    path('coupons/', include('apps.coupons.api_urls')),
    path('notifications/', include('apps.notifications.api_urls')),
    path('analytics/', include('apps.analytics.api_urls')),
    path('support/', include('apps.support.api_urls')),
]
