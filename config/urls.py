"""
ShopSphere - URL Configuration
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Admin site customization
admin.site.site_header = 'ShopSphere Admin'
admin.site.site_title = 'ShopSphere'
admin.site.index_title = 'Marketplace Management'

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # App URLs
    path('', include('apps.core.urls', namespace='core')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('vendors/', include('apps.vendors.urls', namespace='vendors')),
    path('products/', include('apps.products.urls', namespace='products')),
    path('search/', include('apps.search.urls', namespace='search')),
    path('cart/', include('apps.cart.urls', namespace='cart')),
    path('wishlist/', include('apps.wishlist.urls', namespace='wishlist')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
    path('payments/', include('apps.payments.urls', namespace='payments')),
    path('reviews/', include('apps.reviews.urls', namespace='reviews')),
    path('coupons/', include('apps.coupons.urls', namespace='coupons')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('support/', include('apps.support.urls', namespace='support')),
    path('analytics/', include('apps.analytics.urls', namespace='analytics')),
    path('loyalty/', include('apps.loyalty.urls', namespace='loyalty')),
    path('pages/', include('apps.cms.urls', namespace='cms')),

    # API URLs
    path('api/v1/', include('apps.core.api_urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar
        urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    except ImportError:
        pass
