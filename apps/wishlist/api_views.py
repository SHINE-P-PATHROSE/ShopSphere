"""Wishlist serializers and API."""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from apps.products.models import Product
from apps.products.serializers import ProductSerializer
from .models import WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'product_id', 'created_at']


class WishlistListAPIView(generics.ListAPIView):
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return WishlistItem.objects.none()
        return WishlistItem.objects.filter(user=self.request.user).select_related(
            'product', 'product__store'
        )


class WishlistToggleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        item, created = WishlistItem.objects.get_or_create(
            user=request.user, product=product
        )
        if not created:
            item.delete()
            return Response({'added': False})
        return Response({'added': True}, status=status.HTTP_201_CREATED)
