"""Review API URLs."""
from django.urls import path
from .api_views import ReviewCreateAPIView, ProductReviewListAPIView, MarkReviewHelpfulAPIView

urlpatterns = [
    path('', ReviewCreateAPIView.as_view(), name='api-review-create'),
    path('product/<int:product_id>/', ProductReviewListAPIView.as_view(), name='api-reviews'),
    path('<int:pk>/helpful/', MarkReviewHelpfulAPIView.as_view(), name='api-review-helpful'),
]
