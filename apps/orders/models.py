"""Orders Models - Complete order lifecycle management."""
from django.db import models
from apps.core.models import TimeStampedModel
import shortuuid


class Order(TimeStampedModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'), ('PACKED', 'Packed'),
        ('SHIPPED', 'Shipped'), ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'), ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned'), ('REFUNDED', 'Refunded'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'), ('STRIPE', 'Stripe'),
        ('RAZORPAY', 'Razorpay'), ('WALLET', 'Wallet'),
    ]

    user = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='orders', null=True, blank=True)
    order_number = models.CharField(max_length=20, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    shipping_address = models.JSONField()
    billing_address = models.JSONField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    coupon = models.ForeignKey('coupons.Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    shipping_method = models.CharField(max_length=20, default='STANDARD')
    notes = models.TextField(blank=True)
    guest_email = models.EmailField(blank=True)
    is_guest = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['order_number']),
        ]

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"SS-{shortuuid.ShortUUID().random(length=10).upper()}"
        super().save(*args, **kwargs)


class OrderItem(TimeStampedModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'),
        ('SHIPPED', 'Shipped'), ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'), ('RETURNED', 'Returned'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.PROTECT)
    store = models.ForeignKey('vendors.Store', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"{self.variant} x {self.quantity}"

    def save(self, *args, **kwargs):
        self.total = self.price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20)
    changed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)


class ReturnRequest(TimeStampedModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'), ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'), ('COMPLETED', 'Completed'),
    ]
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name='return_request')
    reason = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    admin_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Return for {self.order_item}"


class Refund(TimeStampedModel):
    return_request = models.OneToOneField(ReturnRequest, on_delete=models.CASCADE, related_name='refund')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=[('PENDING','Pending'),('PROCESSED','Processed'),('FAILED','Failed')], default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
