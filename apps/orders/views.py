"""Order web views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView

from apps.cart.services import CartService
from apps.coupons.services import CouponService
from apps.payments.services import PaymentService
from django.conf import settings
from .models import Order, ReturnRequest
from .services import OrderService


class CheckoutView(LoginRequiredMixin, View):
    template_name = 'orders/checkout.html'

    def get(self, request):
        cart = CartService.get_or_create_cart(user=request.user)
        items = CartService.get_active_items(cart)
        if not items:
            messages.warning(request, 'Your cart is empty.')
            return redirect('cart:cart')
        subtotal = CartService.calculate_subtotal(cart)
        totals = OrderService.calculate_totals(cart)
        addresses = request.user.addresses.all()
        return render(request, self.template_name, {
            'cart': cart, 'cart_items': items, 'totals': totals,
            'addresses': addresses,
            'stripe_key': settings.STRIPE_PUBLIC_KEY,
            'razorpay_key': settings.RAZORPAY_KEY_ID,
        })

    def post(self, request):
        cart = CartService.get_or_create_cart(user=request.user)
        address_id = request.POST.get('address_id')
        address = get_object_or_404(request.user.addresses, pk=address_id)
        shipping_address = {
            'full_name': address.full_name, 'phone': address.phone,
            'address_line_1': address.address_line_1,
            'address_line_2': address.address_line_2,
            'city': address.city, 'state': address.state,
            'postal_code': address.postal_code, 'country': address.country,
        }
        try:
            order = OrderService.create_from_cart(
                cart,
                user=request.user,
                shipping_address=shipping_address,
                payment_method=request.POST.get('payment_method', 'COD'),
                coupon_code=request.POST.get('coupon_code', ''),
                shipping_method=request.POST.get('shipping_method', 'STANDARD'),
            )
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('orders:checkout')

        if order.payment_method == 'COD':
            PaymentService.process_cod(order)
        elif order.payment_method == 'STRIPE':
            PaymentService.create_stripe_intent(order)
        elif order.payment_method == 'RAZORPAY':
            PaymentService.create_razorpay_order(order)

        messages.success(request, f'Order #{order.order_number} placed successfully!')
        return redirect('orders:detail', order_number=order.order_number)


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'items', 'status_history'
        )


class ReturnRequestView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        from apps.orders.models import OrderItem
        item = get_object_or_404(OrderItem, pk=item_id, order__user=request.user)
        ReturnRequest.objects.get_or_create(
            order_item=item,
            defaults={
                'reason': request.POST.get('reason', 'Other'),
                'description': request.POST.get('description', ''),
            }
        )
        messages.success(request, 'Return request submitted.')
        return redirect('orders:detail', order_number=item.order.order_number)
