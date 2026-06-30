"""Wishlist web views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views import View

from apps.products.models import Product
from .models import WishlistItem


class WishlistView(LoginRequiredMixin, ListView):
    model = WishlistItem
    template_name = 'wishlist/wishlist.html'
    context_object_name = 'items'

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user).select_related('product')


class ToggleWishlistView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            item.delete()
            messages.info(request, 'Removed from wishlist.')
        else:
            messages.success(request, 'Added to wishlist.')
        return redirect(request.META.get('HTTP_REFERER', 'products:list'))
