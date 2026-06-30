from django.views.generic import CreateView, TemplateView, UpdateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .models import VendorProfile, Store, StorePolicy
from apps.products.models import Product
from apps.orders.models import OrderItem

class VendorRegisterView(LoginRequiredMixin, CreateView):
    model = VendorProfile
    fields = ['business_name', 'business_email', 'business_phone', 'gstin', 'pan', 'bank_name', 'bank_account_number', 'bank_ifsc', 'id_proof', 'address_proof']
    template_name = 'vendors/register.html'
    success_url = reverse_lazy('vendors:dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        # Update user role to VENDOR
        self.request.user.role = 'VENDOR'
        self.request.user.save(update_fields=['role'])
        return response

class VendorDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'vendors/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor_profile = getattr(self.request.user, 'vendor_profile', None)
        if vendor_profile:
            context['vendor'] = vendor_profile
            context['store'] = getattr(vendor_profile, 'store', None)
            if context['store']:
                context['products'] = Product.objects.filter(store=context['store'])
                context['order_items'] = OrderItem.objects.filter(store=context['store'])
        return context

class StoreEditView(LoginRequiredMixin, UpdateView):
    model = Store
    fields = ['name', 'description', 'logo', 'banner', 'tagline']
    template_name = 'vendors/store_edit.html'
    success_url = reverse_lazy('vendors:dashboard')

    def get_object(self, queryset=None):
        return self.request.user.vendor_profile.store

class VendorProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'vendors/product_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.filter(store=self.request.user.vendor_profile.store)

class VendorOrderListView(LoginRequiredMixin, ListView):
    model = OrderItem
    template_name = 'vendors/order_list.html'
    context_object_name = 'order_items'

    def get_queryset(self):
        return OrderItem.objects.filter(store=self.request.user.vendor_profile.store)

class StoreDetailView(DetailView):
    model = Store
    template_name = 'vendors/store_detail.html'
    context_object_name = 'store'
    slug_field = 'slug'
