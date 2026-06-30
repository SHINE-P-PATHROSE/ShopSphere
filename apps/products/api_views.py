from rest_framework import viewsets, generics, permissions
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.core.permissions import IsVendor
from .models import Product, Category, Brand
from .serializers import ProductSerializer, CategorySerializer, BrandSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(status='APPROVED').select_related(
        'store', 'category', 'brand'
    ).prefetch_related('images', 'variants')
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'brand', 'is_featured', 'store']
    search_fields = ['title', 'description']
    ordering_fields = ['base_price', 'created_at', 'sales_count', 'average_rating']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsVendor()]

    def perform_create(self, serializer):
        vendor = self.request.user.vendor_profile
        serializer.save(store=vendor.store)

    def perform_update(self, serializer):
        # Ensure a vendor can only edit their own products
        product = self.get_object()
        if product.store != self.request.user.vendor_profile.store:
            raise PermissionDenied('You can only edit your own products.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.store != self.request.user.vendor_profile.store:
            raise PermissionDenied('You can only delete your own products.')
        instance.soft_delete()


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class BrandListAPIView(generics.ListAPIView):
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    permission_classes = [permissions.AllowAny]
