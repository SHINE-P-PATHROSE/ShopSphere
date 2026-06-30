from django.urls import path
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register('', api_views.ProductViewSet, basename='product')

urlpatterns = [
    path('categories/', api_views.CategoryListAPIView.as_view(), name='api_categories'),
    path('brands/', api_views.BrandListAPIView.as_view(), name='api_brands'),
] + router.urls
