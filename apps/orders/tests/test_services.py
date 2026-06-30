"""Cart and order service tests."""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model

from apps.cart.models import Cart, CartItem
from apps.cart.services import CartService
from apps.orders.services import OrderService
from apps.products.models import Category, Product, ProductVariant
from apps.vendors.models import VendorProfile, Store

User = get_user_model()


@pytest.fixture
def product_setup(db, customer_user):
    vendor_user = User.objects.create_user(
        email='v@test.com', password='pass', first_name='V', last_name='S',
        role='VENDOR', is_verified=True,
    )
    vp = VendorProfile.objects.create(
        user=vendor_user, business_name='Test Store',
        business_email='v@test.com', business_phone='1234567890', status='APPROVED',
    )
    # Store is auto-created by the create_store_on_approval signal
    store = vp.store
    cat = Category.objects.create(name='Test Cat', slug='test-cat')
    product = Product.objects.create(
        store=store, category=cat, title='Test Product', slug='test-product',
        description='Test', base_price=Decimal('100'), status='APPROVED',
    )
    variant = ProductVariant.objects.create(
        product=product, sku='TEST-SKU-001', price=Decimal('100'), stock=10,
    )
    return variant


@pytest.mark.django_db
class TestCartService:
    def test_add_item(self, customer_user, product_setup):
        cart = CartService.get_or_create_cart(user=customer_user)
        CartService.add_item(cart, product_setup, 2)
        assert cart.items.count() == 1
        assert cart.items.first().quantity == 2

    def test_stock_validation(self, customer_user, product_setup):
        cart = CartService.get_or_create_cart(user=customer_user)
        with pytest.raises(ValueError):
            CartService.add_item(cart, product_setup, 100)


@pytest.mark.django_db
class TestOrderService:
    def test_create_order(self, customer_user, product_setup):
        cart = CartService.get_or_create_cart(user=customer_user)
        CartService.add_item(cart, product_setup, 1)
        order = OrderService.create_from_cart(
            cart, user=customer_user,
            shipping_address={'city': 'Mumbai'},
            payment_method='COD',
        )
        assert order.total > 0
        assert order.items.count() == 1
        product_setup.refresh_from_db()
        assert product_setup.stock == 9
