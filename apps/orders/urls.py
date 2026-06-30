"""Order URLs."""
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    # NOTE: specific paths must come before the generic <str:order_number> catch-all
    path('return/<int:item_id>/', views.ReturnRequestView.as_view(), name='return'),
    path('', views.OrderListView.as_view(), name='list'),
    path('<str:order_number>/', views.OrderDetailView.as_view(), name='detail'),
]
