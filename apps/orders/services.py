"""Order service layer - checkout and order lifecycle."""
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.cart.services import CartService
from apps.coupons.services import CouponService
from apps.notifications.services import NotificationService
from .models import Order, OrderItem, OrderStatusHistory


class OrderService:
    """Create and manage orders from cart."""

    GST_RATE = Decimal(str(getattr(settings, 'GST_RATE', 18.0)))

    @staticmethod
    def _shipping_cost(method):
        if method == 'EXPRESS':
            return Decimal(str(settings.EXPRESS_SHIPPING_COST))
        return Decimal(str(settings.STANDARD_SHIPPING_COST))

    @classmethod
    def calculate_totals(cls, cart, coupon=None, shipping_method='STANDARD'):
        subtotal = Decimal(str(CartService.calculate_subtotal(cart)))
        discount = Decimal('0')
        if coupon:
            discount = CouponService.calculate_discount(coupon, subtotal)
        taxable = subtotal - discount
        tax = (taxable * cls.GST_RATE / Decimal('100')).quantize(Decimal('0.01'))
        shipping = cls._shipping_cost(shipping_method)
        total = (taxable + tax + shipping).quantize(Decimal('0.01'))
        return {
            'subtotal': subtotal,
            'discount_amount': discount,
            'tax_amount': tax,
            'shipping_cost': shipping,
            'total': total,
        }

    @classmethod
    @transaction.atomic
    def create_from_cart(
        cls,
        cart,
        user=None,
        shipping_address=None,
        billing_address=None,
        payment_method='COD',
        coupon_code=None,
        shipping_method='STANDARD',
        guest_email='',
        notes='',
    ):
        errors = CartService.validate_stock(cart)
        if errors:
            raise ValueError('; '.join(errors))

        items = list(CartService.get_active_items(cart))
        if not items:
            raise ValueError('Cart is empty')

        store_ids = {item.variant.product.store_id for item in items}
        coupon = None
        if coupon_code:
            subtotal = CartService.calculate_subtotal(cart)
            coupon, err = CouponService.validate_coupon(
                coupon_code, user, subtotal, store_ids
            )
            if err:
                raise ValueError(err)

        totals = cls.calculate_totals(cart, coupon, shipping_method)
        order = Order.objects.create(
            user=user if user and user.is_authenticated else None,
            shipping_address=shipping_address,
            billing_address=billing_address or shipping_address,
            subtotal=totals['subtotal'],
            tax_amount=totals['tax_amount'],
            shipping_cost=totals['shipping_cost'],
            discount_amount=totals['discount_amount'],
            total=totals['total'],
            payment_method=payment_method,
            coupon=coupon,
            shipping_method=shipping_method,
            guest_email=guest_email,
            is_guest=not (user and user.is_authenticated),
            notes=notes,
            status='PENDING',
        )

        for item in items:
            variant = item.variant
            if variant.stock < item.quantity:
                raise ValueError(f'Insufficient stock for {variant.product.title}')
            variant.stock -= item.quantity
            variant.save(update_fields=['stock'])
            OrderItem.objects.create(
                order=order,
                variant=variant,
                store=variant.product.store,
                quantity=item.quantity,
                price=variant.price,
                total=variant.price * item.quantity,
            )

        if coupon and user:
            CouponService.record_usage(coupon, user, order, totals['discount_amount'])

        OrderStatusHistory.objects.create(
            order=order, status='PENDING',
            changed_by=user if user and user.is_authenticated else None,
            notes='Order placed',
        )

        CartService.clear_active_items(cart)

        if user and user.is_authenticated:
            NotificationService.notify_order_created(user, order)

        return order

    @staticmethod
    @transaction.atomic
    def update_status(order, new_status, changed_by=None, notes=''):
        old_status = order.status
        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])
        OrderStatusHistory.objects.create(
            order=order, status=new_status, changed_by=changed_by, notes=notes
        )
        if order.user:
            NotificationService.notify_order_status(order.user, order, new_status)
        return order

    @staticmethod
    def confirm_payment(order):
        return OrderService.update_status(
            order, 'CONFIRMED', notes='Payment confirmed'
        )
