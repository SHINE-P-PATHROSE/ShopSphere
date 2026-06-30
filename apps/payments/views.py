"""Payment views and webhooks."""
import json
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from apps.orders.models import Order
from .models import Payment
from .services import PaymentService


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    def post(self, request):
        payload = request.body
        sig = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        ok = PaymentService.handle_stripe_webhook(payload, sig)
        return HttpResponse(status=200 if ok else 400)


class RazorpayVerifyView(LoginRequiredMixin, View):
    def post(self, request):
        order_id = request.POST.get('razorpay_order_id')
        payment_id = request.POST.get('razorpay_payment_id')
        signature = request.POST.get('razorpay_signature')
        if PaymentService.verify_razorpay_payment(order_id, payment_id, signature):
            payment = get_object_or_404(Payment, transaction_id=order_id)
            messages.success(request, 'Payment successful!')
            return redirect('orders:detail', order_number=payment.order.order_number)
        messages.error(request, 'Payment verification failed.')
        return redirect('orders:list')


class PaymentRetryView(LoginRequiredMixin, View):
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        if order.payment_method == 'STRIPE':
            PaymentService.create_stripe_intent(order)
        elif order.payment_method == 'RAZORPAY':
            PaymentService.create_razorpay_order(order)
        messages.info(request, 'Payment retry initiated.')
        return redirect('orders:detail', order_number=order_number)
