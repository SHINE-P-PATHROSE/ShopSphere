"""Payment gateway integration services."""
import logging
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

import stripe

from apps.orders.services import OrderService
from .models import Payment, WebhookLog

logger = logging.getLogger(__name__)


class PaymentService:
    """Handle Stripe, Razorpay, and COD payments."""

    @staticmethod
    def create_payment_record(order):
        return Payment.objects.create(
            order=order,
            gateway=order.payment_method,
            amount=order.total,
            status='PENDING' if order.payment_method != 'COD' else 'SUCCESS',
        )

    @staticmethod
    def create_stripe_intent(order):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
            amount=int(order.total * 100),
            currency='inr',
            metadata={'order_number': order.order_number},
            automatic_payment_methods={'enabled': True},
        )
        payment = PaymentService.create_payment_record(order)
        payment.transaction_id = intent.id
        payment.gateway_response = {'client_secret': intent.client_secret}
        payment.save()
        return intent.client_secret, payment

    @staticmethod
    def create_razorpay_order(order):
        import razorpay
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        razorpay_order = client.order.create({
            'amount': int(order.total * 100),
            'currency': 'INR',
            'receipt': order.order_number,
        })
        payment = PaymentService.create_payment_record(order)
        payment.transaction_id = razorpay_order['id']
        payment.gateway_response = razorpay_order
        payment.save()
        return razorpay_order, payment

    @staticmethod
    def mark_success(payment, transaction_id='', response=None):
        payment.status = 'SUCCESS'
        payment.transaction_id = transaction_id or payment.transaction_id
        payment.paid_at = timezone.now()
        if response:
            payment.gateway_response = response
        payment.save()
        OrderService.confirm_payment(payment.order)

    @staticmethod
    def mark_failed(payment, response=None):
        payment.status = 'FAILED'
        if response:
            payment.gateway_response = response
        payment.save()

    @staticmethod
    def handle_stripe_webhook(payload, sig_header):
        WebhookLog.objects.create(gateway='STRIPE', event_type='webhook', payload=payload)
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.error('Stripe webhook error: %s', e)
            return False

        if event['type'] == 'payment_intent.succeeded':
            intent = event['data']['object']
            try:
                payment = Payment.objects.get(transaction_id=intent['id'])
                PaymentService.mark_success(payment, intent['id'], intent)
            except Payment.DoesNotExist:
                logger.warning('Payment not found for intent %s', intent['id'])
        return True

    @staticmethod
    def verify_razorpay_payment(order_id, payment_id, signature):
        import razorpay
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,
            })
            payment = Payment.objects.get(transaction_id=order_id)
            PaymentService.mark_success(payment, payment_id)
            return True
        except Exception as e:
            logger.error('Razorpay verification failed: %s', e)
            try:
                payment = Payment.objects.get(transaction_id=order_id)
                PaymentService.mark_failed(payment)
            except Payment.DoesNotExist:
                pass
            return False

    @staticmethod
    def process_cod(order):
        payment = PaymentService.create_payment_record(order)
        payment.status = 'SUCCESS'
        payment.paid_at = timezone.now()
        payment.transaction_id = f'COD-{order.order_number}'
        payment.save()
        OrderService.confirm_payment(order)
        return payment
