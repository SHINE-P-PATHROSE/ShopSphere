"""Product API tests."""
import pytest
from decimal import Decimal
from apps.products.models import Category, Product, ProductVariant
from apps.vendors.models import VendorProfile, Store
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def approved_product(db):
    user = User.objects.create_user(
        email='v2@test.com', password='pass', first_name='V', last_name='2',
        role='VENDOR', is_verified=True,
    )
    vp = VendorProfile.objects.create(
        user=user, business_name='Shop', business_email='v2@test.com',
        business_phone='9999999999', status='APPROVED',
    )
    # Store is auto-created by the create_store_on_approval signal
    store = vp.store
    cat = Category.objects.create(name='Cat', slug='cat')
    p = Product.objects.create(
        store=store, category=cat, title='Widget', slug='widget',
        description='A widget', base_price=Decimal('50'), status='APPROVED',
    )
    ProductVariant.objects.create(product=p, sku='W-001', price=Decimal('50'), stock=5)
    return p


@pytest.mark.django_db
class TestProductAPI:
    def test_list_products(self, api_client, approved_product):
        response = api_client.get('/api/v1/products/')
        assert response.status_code == 200

    def test_product_detail(self, api_client, approved_product):
        response = api_client.get(f'/api/v1/products/{approved_product.id}/')
        assert response.status_code == 200
        assert response.data['title'] == 'Widget'
