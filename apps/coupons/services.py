"""Coupon service layer."""
from decimal import Decimal
from django.utils import timezone

from .models import Coupon, CouponUsage


class CouponService:
    """Validate and apply discount coupons."""

    @staticmethod
    def validate_coupon(code, user, subtotal, store_ids=None):
        try:
            coupon = Coupon.objects.get(code__iexact=code.strip())
        except Coupon.DoesNotExist:
            return None, 'Invalid coupon code'

        if not coupon.is_valid:
            return None, 'Coupon has expired or is no longer valid'

        if subtotal < coupon.min_order_amount:
            return None, f'Minimum order amount is ₹{coupon.min_order_amount}'

        if coupon.vendor_id and store_ids and coupon.vendor_id not in store_ids:
            return None, 'Coupon not valid for items in your cart'

        user_usage = CouponUsage.objects.filter(coupon=coupon, user=user).count()
        if user and user_usage >= coupon.per_user_limit:
            return None, 'You have already used this coupon'

        return coupon, None

    @staticmethod
    def calculate_discount(coupon, subtotal):
        if coupon.discount_type == 'PERCENTAGE':
            discount = subtotal * (coupon.discount_value / Decimal('100'))
            if coupon.max_discount:
                discount = min(discount, coupon.max_discount)
        else:
            discount = coupon.discount_value
        return min(discount, subtotal).quantize(Decimal('0.01'))

    @staticmethod
    def record_usage(coupon, user, order, discount_amount):
        CouponUsage.objects.create(
            coupon=coupon, user=user, order=order, discount_amount=discount_amount
        )
        coupon.times_used += 1
        coupon.save(update_fields=['times_used'])
