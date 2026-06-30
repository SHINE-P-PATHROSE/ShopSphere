"""Seed demo data for ShopSphere."""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo categories, brands, vendors, and products'

    def handle(self, *args, **options):
        from apps.products.models import (
            Category, Brand, Product, ProductVariant, ProductAttribute,
            ProductAttributeValue,
        )
        from apps.vendors.models import VendorProfile, Store
        from apps.coupons.models import Coupon
        from django.utils import timezone
        from datetime import timedelta

        self.stdout.write('Seeding ShopSphere demo data...')

        admin, _ = User.objects.get_or_create(
            email='admin@shopsphere.com',
            defaults={
                'first_name': 'Admin', 'last_name': 'User',
                'role': 'ADMIN', 'is_staff': True, 'is_superuser': True,
                'is_verified': True,
            },
        )
        if not admin.has_usable_password():
            admin.set_password('Admin@12345')
            admin.save()

        customer, _ = User.objects.get_or_create(
            email='customer@shopsphere.com',
            defaults={'first_name': 'Demo', 'last_name': 'Customer', 'is_verified': True},
        )
        if not customer.has_usable_password():
            customer.set_password('Customer@123')
            customer.save()

        categories_data = [
            ('Electronics', '📱'), ('Fashion', '👕'), ('Home & Kitchen', '🏠'),
            ('Books', '📚'), ('Sports', '⚽'),
        ]
        categories = []
        for name, icon in categories_data:
            cat, _ = Category.objects.get_or_create(
                slug=slugify(name), defaults={'name': name, 'icon': icon}
            )
            categories.append(cat)

        brands = []
        for name in ['TechPro', 'StyleHub', 'HomeEssentials', 'FitLife']:
            b, _ = Brand.objects.get_or_create(slug=slugify(name), defaults={'name': name})
            brands.append(b)

        vendor_user, _ = User.objects.get_or_create(
            email='vendor@shopsphere.com',
            defaults={'first_name': 'Demo', 'last_name': 'Vendor', 'role': 'VENDOR', 'is_verified': True},
        )
        if not vendor_user.has_usable_password():
            vendor_user.set_password('Vendor@123')
            vendor_user.save()

        vendor_profile, _ = VendorProfile.objects.get_or_create(
            user=vendor_user,
            defaults={
                'business_name': 'Demo Store',
                'business_email': 'vendor@shopsphere.com',
                'business_phone': '9876543210',
                'status': 'APPROVED',
            },
        )
        vendor_profile.status = 'APPROVED'
        vendor_profile.save()

        store, _ = Store.objects.get_or_create(
            vendor=vendor_profile,
            defaults={'name': 'Demo Store', 'slug': 'demo-store', 'description': 'Quality products at great prices'},
        )

        size_attr, _ = ProductAttribute.objects.get_or_create(name='Size')
        sizes = []
        for s in ['S', 'M', 'L', 'XL']:
            av, _ = ProductAttributeValue.objects.get_or_create(attribute=size_attr, value=s)
            sizes.append(av)

        products_data = [
            ('Wireless Bluetooth Headphones', Decimal('1999'), Decimal('2999'), categories[0], brands[0]),
            ('Premium Cotton T-Shirt', Decimal('599'), Decimal('999'), categories[1], brands[1]),
            ('Non-Stick Cookware Set', Decimal('2499'), None, categories[2], brands[2]),
            ('Running Shoes Pro', Decimal('3499'), Decimal('4999'), categories[4], brands[3]),
            ('Python Programming Book', Decimal('499'), None, categories[3], brands[0]),
            ('Smart Watch Series X', Decimal('4999'), Decimal('6999'), categories[0], brands[0]),
            ('Denim Jacket Classic', Decimal('1899'), Decimal('2499'), categories[1], brands[1]),
            ('Yoga Mat Premium', Decimal('799'), None, categories[4], brands[3]),
        ]

        for i, (title, price, compare, cat, brand) in enumerate(products_data):
            slug = slugify(title)
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'store': store, 'category': cat, 'brand': brand,
                    'title': title, 'description': f'High quality {title}. Perfect for everyday use.',
                    'short_description': f'Best-selling {title}',
                    'base_price': price, 'compare_price': compare,
                    'status': 'APPROVED', 'is_featured': i < 4,
                },
            )
            if created:
                for j, size in enumerate(sizes[:3]):
                    variant = ProductVariant.objects.create(
                        product=product,
                        sku=f'SKU-{slug[:8].upper()}-{size.value}',
                        price=price + (j * 100),
                        compare_price=compare,
                        stock=50 - j * 5,
                    )
                    variant.attribute_values.add(size)

        Coupon.objects.get_or_create(
            code='WELCOME10',
            defaults={
                'discount_type': 'PERCENTAGE',
                'discount_value': Decimal('10'),
                'min_order_amount': Decimal('500'),
                'max_discount': Decimal('500'),
                'valid_from': timezone.now() - timedelta(days=1),
                'valid_to': timezone.now() + timedelta(days=365),
                'usage_limit': 1000,
                'description': '10% off on your first order',
            },
        )

        self.stdout.write(self.style.SUCCESS(
            'Demo data seeded!\n'
            '  Admin: admin@shopsphere.com / Admin@12345\n'
            '  Customer: customer@shopsphere.com / Customer@123\n'
            '  Vendor: vendor@shopsphere.com / Vendor@123\n'
            '  Coupon: WELCOME10'
        ))
