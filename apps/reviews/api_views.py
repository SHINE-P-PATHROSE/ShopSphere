"""Review API views."""
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.products.models import Product
from .models import Review
from .serializers import ReviewSerializer, ReviewCreateSerializer
from .services import ReviewService


class ProductReviewListAPIView(generics.ListAPIView):
    """List all approved reviews for a given product."""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Review.objects.none()  # overridden below; satisfies drf-spectacular

    def get_queryset(self):
        return Review.objects.filter(
            product_id=self.kwargs.get('product_id'), is_approved=True
        ).select_related('user').prefetch_related('images')


class ReviewCreateAPIView(generics.CreateAPIView):
    """Submit a review (verified buyers only)."""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        ser = ReviewCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        try:
            product = Product.objects.get(pk=ser.validated_data['product_id'])
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            review = ReviewService.create_review(
                request.user,
                product,
                ser.validated_data['rating'],
                ser.validated_data['body'],
                ser.validated_data.get('title', ''),
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class MarkReviewHelpfulAPIView(generics.UpdateAPIView):
    """Increment the helpful_count on a review."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReviewSerializer
    queryset = Review.objects.filter(is_approved=True)

    def update(self, request, *args, **kwargs):
        review = self.get_object()
        Review.objects.filter(pk=review.pk).update(helpful_count=review.helpful_count + 1)
        return Response({'helpful_count': review.helpful_count + 1})
