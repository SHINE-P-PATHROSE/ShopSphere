from django.urls import path
from . import api_views
urlpatterns = [
    path('', api_views.VendorListAPIView.as_view(), name='api_vendor_list'),
    path('<int:pk>/', api_views.VendorDetailAPIView.as_view(), name='api_vendor_detail'),
    path('store/<slug:slug>/', api_views.StoreAPIView.as_view(), name='api_store'),
]
