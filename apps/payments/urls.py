from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('webhooks/stripe/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    path('razorpay/verify/', views.RazorpayVerifyView.as_view(), name='razorpay-verify'),
    path('retry/<str:order_number>/', views.PaymentRetryView.as_view(), name='retry'),
]
