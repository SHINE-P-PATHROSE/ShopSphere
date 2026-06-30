"""Cart Models - Shopping cart with save-for-later."""
from django.db import models
from apps.core.models import TimeStampedModel


class Cart(TimeStampedModel):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, db_index=True)

    def __str__(self):
        return f"Cart for {self.user or self.session_key}"

    @property
    def total_items(self):
        return self.items.filter(saved_for_later=False).count()

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.filter(saved_for_later=False))


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    saved_for_later = models.BooleanField(default=False)

    class Meta:
        unique_together = ['cart', 'variant']

    def __str__(self):
        return f"{self.variant} x {self.quantity}"

    @property
    def line_total(self):
        return self.variant.price * self.quantity
