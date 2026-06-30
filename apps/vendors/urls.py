from django.urls import path
from . import views
app_name = 'vendors'
urlpatterns = [
    path('register/', views.VendorRegisterView.as_view(), name='register'),
    path('dashboard/', views.VendorDashboardView.as_view(), name='dashboard'),
    path('store/edit/', views.StoreEditView.as_view(), name='store_edit'),
    path('products/', views.VendorProductListView.as_view(), name='products'),
    path('orders/', views.VendorOrderListView.as_view(), name='orders'),
    path('store/<slug:slug>/', views.StoreDetailView.as_view(), name='store_detail'),
]
