"""Product web views."""
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404

from .models import Product, Category, Brand


class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        return Product.objects.filter(status='APPROVED').select_related(
            'store', 'category', 'brand'
        ).prefetch_related('images')


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'

    def get_queryset(self):
        return Product.objects.filter(status='APPROVED').select_related(
            'store', 'category', 'brand'
        ).prefetch_related('images', 'variants', 'variants__attribute_values')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Increment view count once — avoid double-hit from get_context_data
        Product.objects.filter(pk=obj.pk).update(views_count=obj.views_count + 1)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object  # already fetched — no second DB hit
        context['variants'] = product.variants.filter(is_active=True)
        context['related_products'] = Product.objects.filter(
            category=product.category, status='APPROVED'
        ).exclude(pk=product.pk).select_related('store')[:4]
        return context


class CategoryProductsView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        # get_object_or_404 instead of bare .get() → proper 404 on bad slug
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'], is_active=True)
        return Product.objects.filter(
            category=self.category, status='APPROVED'
        ).select_related('store', 'brand').prefetch_related('images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class BrandProductsView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        # get_object_or_404 instead of bare .get() → proper 404 on bad slug
        self.brand = get_object_or_404(Brand, slug=self.kwargs['slug'], is_active=True)
        return Product.objects.filter(
            brand=self.brand, status='APPROVED'
        ).select_related('store', 'category').prefetch_related('images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brand'] = self.brand
        return context
