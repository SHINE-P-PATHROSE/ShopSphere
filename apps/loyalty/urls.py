from django.urls import path
from . import views

app_name = 'loyalty'

urlpatterns = [
    path('', views.LoyaltyDashboardView.as_view(), name='dashboard'),
]
