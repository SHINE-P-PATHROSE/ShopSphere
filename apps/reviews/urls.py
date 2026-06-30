"""Review URLs."""
from django.urls import path
from . import api_views, views

app_name = 'reviews'

urlpatterns = [
    path('product/<int:product_id>/', views.ProductReviewView.as_view(), name='product'),
]

api_urlpatterns = [
    path('', api_views.ReviewCreateAPIView.as_view(), name='api-review-create'),
    path('product/<int:product_id>/', api_views.ProductReviewListAPIView.as_view(), name='api-reviews'),
]
