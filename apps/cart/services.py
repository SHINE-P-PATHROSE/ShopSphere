"""Cart service layer."""
from decimal import Decimal
from django.db import transaction

from .models import Cart, CartItem


class CartService:
    """Business logic for shopping cart operations."""

    @staticmethod
    def get_or_create_cart(user=None, session_key=None):
        if user and user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=user)
            return cart
        if session_key:
            cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
            return cart
        raise ValueError('User or session_key required')

    @staticmethod
    def merge_guest_cart(user, session_key):
        """Merge guest session cart into authenticated user cart."""
        if not session_key or not user.is_authenticated:
            return
        try:
            guest_cart = Cart.objects.get(session_key=session_key, user=None)
        except Cart.DoesNotExist:
            return

        user_cart, _ = Cart.objects.get_or_create(user=user)
        with transaction.atomic():
            for item in guest_cart.items.all():
                existing = user_cart.items.filter(variant=item.variant).first()
                if existing:
                    existing.quantity += item.quantity
                    existing.save()
                    item.delete()
                else:
                    item.cart = user_cart
                    item.save()
            guest_cart.delete()

    @staticmethod
    def add_item(cart, variant, quantity=1):
        if not variant.is_in_stock:
            raise ValueError('Product is out of stock')
        if variant.stock < quantity:
            raise ValueError(f'Only {variant.stock} units available')

        item, created = CartItem.objects.get_or_create(cart=cart, variant=variant)
        new_qty = quantity if created else item.quantity + quantity
        if variant.stock < new_qty:
            raise ValueError(f'Cannot add more than {variant.stock} units')
        item.quantity = new_qty
        item.saved_for_later = False
        item.save()
        return item

    @staticmethod
    def get_active_items(cart):
        return cart.items.filter(saved_for_later=False).select_related(
            'variant', 'variant__product', 'variant__product__store'
        )

    @staticmethod
    def calculate_subtotal(cart):
        return sum(item.line_total for item in CartService.get_active_items(cart))

    @staticmethod
    def validate_stock(cart):
        errors = []
        for item in CartService.get_active_items(cart):
            if not item.variant.is_in_stock:
                errors.append(f'{item.variant.product.title} is out of stock')
            elif item.variant.stock < item.quantity:
                errors.append(
                    f'{item.variant.product.title}: only {item.variant.stock} available'
                )
        return errors

    @staticmethod
    def clear_active_items(cart):
        cart.items.filter(saved_for_later=False).delete()
