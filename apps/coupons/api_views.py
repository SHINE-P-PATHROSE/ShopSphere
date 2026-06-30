"""Coupon API."""
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.services import CartService
from .models import Coupon
from .services import CouponService


class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=20)


class CouponValidateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get('code', '')
        cart = CartService.get_or_create_cart(user=request.user)
        subtotal = CartService.calculate_subtotal(cart)
        store_ids = {
            item.variant.product.store_id
            for item in CartService.get_active_items(cart)
        }
        coupon, err = CouponService.validate_coupon(code, request.user, subtotal, store_ids)
        if err:
            return Response({'valid': False, 'error': err}, status=400)
        discount = CouponService.calculate_discount(coupon, subtotal)
        return Response({
            'valid': True,
            'code': coupon.code,
            'discount_amount': discount,
            'discount_type': coupon.discount_type,
        })
