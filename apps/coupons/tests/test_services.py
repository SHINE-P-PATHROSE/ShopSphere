"""Coupon service tests."""
import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from apps.coupons.models import Coupon
from apps.coupons.services import CouponService


@pytest.mark.django_db
class TestCouponService:
    @pytest.fixture
    def coupon(self, db):
        return Coupon.objects.create(
            code='TEST20',
            discount_type='PERCENTAGE',
            discount_value=Decimal('20'),
            min_order_amount=Decimal('100'),
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=30),
        )

    def test_validate_valid_coupon(self, coupon, customer_user):
        c, err = CouponService.validate_coupon('TEST20', customer_user, Decimal('500'))
        assert c is not None
        assert err is None

    def test_calculate_percentage_discount(self, coupon):
        discount = CouponService.calculate_discount(coupon, Decimal('1000'))
        assert discount == Decimal('200.00')

    def test_invalid_coupon(self, customer_user):
        c, err = CouponService.validate_coupon('INVALID', customer_user, Decimal('500'))
        assert c is None
        assert err is not None
