"""Product recommendation engine."""
from django.db.models import Count, Q
from django.core.cache import cache

from apps.products.models import Product


class RecommendationService:
    """Related products, trending, and personalized recommendations."""

    CACHE_TTL = 3600

    @staticmethod
    def related_products(product, limit=8):
        cache_key = f'related_{product.id}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        qs = Product.objects.filter(
            status='APPROVED',
            category=product.category,
        ).exclude(id=product.id).select_related('store', 'brand')[:limit]

        if qs.count() < limit and product.brand_id:
            brand_qs = Product.objects.filter(
                status='APPROVED', brand=product.brand
            ).exclude(id=product.id).select_related('store', 'brand')[:limit]
            qs = (qs | brand_qs).distinct()[:limit]

        cache.set(cache_key, list(qs), RecommendationService.CACHE_TTL)
        return qs

    @staticmethod
    def trending_products(limit=12):
        cache_key = 'trending_products'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        qs = Product.objects.filter(status='APPROVED').order_by(
            '-sales_count', '-views_count'
        ).select_related('store', 'brand')[:limit]
        cache.set(cache_key, list(qs), RecommendationService.CACHE_TTL)
        return qs

    @staticmethod
    def frequently_bought_together(product, limit=4):
        from apps.orders.models import OrderItem
        order_ids = OrderItem.objects.filter(
            variant__product=product
        ).values_list('order_id', flat=True)

        related = OrderItem.objects.filter(
            order_id__in=order_ids
        ).exclude(
            variant__product=product
        ).values('variant__product').annotate(
            freq=Count('id')
        ).order_by('-freq')[:limit]

        product_ids = [r['variant__product'] for r in related]
        return Product.objects.filter(
            id__in=product_ids, status='APPROVED'
        ).select_related('store', 'brand')

    @staticmethod
    def personalized_for_user(user, limit=12):
        if not user or not user.is_authenticated:
            return RecommendationService.trending_products(limit)

        from apps.orders.models import OrderItem
        category_ids = OrderItem.objects.filter(
            order__user=user
        ).values_list('variant__product__category_id', flat=True).distinct()

        if not category_ids:
            return RecommendationService.trending_products(limit)

        return Product.objects.filter(
            status='APPROVED',
            category_id__in=category_ids,
        ).order_by('-average_rating', '-sales_count').select_related(
            'store', 'brand'
        )[:limit]
