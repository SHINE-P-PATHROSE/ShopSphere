"""Cart API views."""
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.products.models import ProductVariant
from .models import CartItem
from .serializers import CartSerializer, CartItemSerializer
from .services import CartService


class CartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get_cart(self, request):
        return CartService.get_or_create_cart(user=request.user)

    @extend_schema(responses=CartSerializer)
    def get(self, request):
        cart = self._get_cart(request)
        return Response(CartSerializer(cart).data)

    @extend_schema(request=CartItemSerializer, responses=CartSerializer)
    def post(self, request):
        cart = self._get_cart(request)
        variant_id = request.data.get('variant_id')
        quantity = int(request.data.get('quantity', 1))
        variant = ProductVariant.objects.select_related('product').get(id=variant_id)
        try:
            CartService.add_item(cart, variant, quantity)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class CartItemDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        cart = CartService.get_or_create_cart(user=request.user)
        try:
            item = CartItem.objects.get(pk=pk, cart=cart)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)
        quantity = request.data.get('quantity')
        saved = request.data.get('saved_for_later')
        if quantity is not None:
            quantity = int(quantity)
            if quantity <= 0:
                item.delete()
                return Response({'message': 'Item removed'})
            if item.variant.stock < quantity:
                return Response({'error': 'Insufficient stock'}, status=400)
            item.quantity = quantity
        if saved is not None:
            item.saved_for_later = bool(saved)
        item.save()
        return Response(CartItemSerializer(item).data)

    def delete(self, request, pk):
        cart = CartService.get_or_create_cart(user=request.user)
        CartItem.objects.filter(pk=pk, cart=cart).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
