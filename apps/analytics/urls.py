from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('admin/', views.AdminDashboardView.as_view(), name='admin'),
    path('vendor/', views.VendorAnalyticsView.as_view(), name='vendor'),
]
