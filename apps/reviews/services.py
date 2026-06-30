"""Review service layer."""
from decimal import Decimal
from django.db.models import Avg, Count

from apps.products.models import Product
from .models import Review


class ReviewService:
    """Manage product reviews and ratings."""

    @staticmethod
    def can_review(user, product):
        if Review.objects.filter(user=user, product=product).exists():
            return False, 'You have already reviewed this product'
        from apps.orders.models import OrderItem
        purchased = OrderItem.objects.filter(
            order__user=user,
            variant__product=product,
            order__status='DELIVERED',
        ).exists()
        if not purchased:
            return False, 'Only verified buyers can review this product'
        return True, None

    @staticmethod
    def create_review(user, product, rating, body, title='', order_item=None):
        ok, err = ReviewService.can_review(user, product)
        if not ok:
            raise ValueError(err)

        review = Review.objects.create(
            user=user,
            product=product,
            rating=rating,
            title=title,
            body=body,
            order_item=order_item,
            is_verified_purchase=True,
        )
        ReviewService._update_product_stats(product)
        return review

    @staticmethod
    def _update_product_stats(product):
        stats = Review.objects.filter(product=product, is_approved=True).aggregate(
            avg=Avg('rating'), count=Count('id')
        )
        product.average_rating = Decimal(str(stats['avg'] or 0)).quantize(Decimal('0.01'))
        product.total_reviews = stats['count']
        product.save(update_fields=['average_rating', 'total_reviews'])
