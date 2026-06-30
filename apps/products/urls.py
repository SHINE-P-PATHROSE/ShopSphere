from django.urls import path
from . import views
app_name = 'products'
urlpatterns = [
    path('', views.ProductListView.as_view(), name='list'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='detail'),
    path('category/<slug:slug>/', views.CategoryProductsView.as_view(), name='by_category'),
    path('brand/<slug:slug>/', views.BrandProductsView.as_view(), name='by_brand'),
]
