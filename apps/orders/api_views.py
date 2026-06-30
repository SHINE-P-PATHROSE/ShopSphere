"""Order API views."""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.services import CartService
from apps.payments.services import PaymentService
from .models import Order, ReturnRequest, OrderItem
from .serializers import OrderSerializer, CheckoutSerializer, ReturnRequestSerializer
from .services import OrderService


class OrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user).prefetch_related('items', 'status_history')


class OrderDetailAPIView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'order_number'

    def get_queryset(self):
        qs = Order.objects.prefetch_related('items', 'status_history')
        if self.request.user.role != 'ADMIN':
            qs = qs.filter(user=self.request.user)
        return qs


class CheckoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        cart = CartService.get_or_create_cart(user=request.user)
        try:
            order = OrderService.create_from_cart(
                cart, user=request.user, **data
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if data['payment_method'] == 'COD':
            PaymentService.process_cod(order)
            client_secret = None
        elif data['payment_method'] == 'STRIPE':
            client_secret, _ = PaymentService.create_stripe_intent(order)
        else:
            razorpay_order, _ = PaymentService.create_razorpay_order(order)
            client_secret = razorpay_order

        return Response({
            'order': OrderSerializer(order).data,
            'payment': client_secret,
        }, status=status.HTTP_201_CREATED)


class ReturnRequestCreateAPIView(generics.CreateAPIView):
    serializer_class = ReturnRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        item = serializer.validated_data['order_item']
        if item.order.user != self.request.user:
            raise permissions.PermissionDenied()
        serializer.save()
