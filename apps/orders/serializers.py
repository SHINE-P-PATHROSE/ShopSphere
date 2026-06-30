"""Order serializers."""
from rest_framework import serializers
from apps.products.serializers import ProductVariantSerializer
from .models import Order, OrderItem, OrderStatusHistory, ReturnRequest


class OrderItemSerializer(serializers.ModelSerializer):
    variant = ProductVariantSerializer(read_only=True)
    product_title = serializers.CharField(source='variant.product.title', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'variant', 'product_title', 'store_name', 'quantity',
                  'price', 'total', 'status']


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ['status', 'notes', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'status', 'shipping_address', 'billing_address',
                  'subtotal', 'tax_amount', 'shipping_cost', 'discount_amount', 'total',
                  'payment_method', 'shipping_method', 'items', 'status_history', 'created_at']


class CheckoutSerializer(serializers.Serializer):
    shipping_address = serializers.JSONField()
    billing_address = serializers.JSONField(required=False)
    payment_method = serializers.ChoiceField(choices=['COD', 'STRIPE', 'RAZORPAY'])
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    shipping_method = serializers.ChoiceField(choices=['STANDARD', 'EXPRESS'], default='STANDARD')
    guest_email = serializers.EmailField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class ReturnRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnRequest
        fields = ['id', 'order_item', 'reason', 'description', 'status', 'created_at']
        read_only_fields = ['status']
