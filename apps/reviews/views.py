"""Review web views."""
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views import View

from apps.products.models import Product
from .models import Review
from .services import ReviewService


class ProductReviewView(ListView):
    model = Review
    template_name = 'reviews/product_reviews.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        return Review.objects.filter(
            product_id=self.kwargs['product_id'], is_approved=True
        ).select_related('user')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['product'] = get_object_or_404(Product, pk=self.kwargs['product_id'])
        return ctx


class SubmitReviewView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        try:
            ReviewService.create_review(
                request.user, product,
                int(request.POST.get('rating', 5)),
                request.POST.get('body', ''),
                request.POST.get('title', ''),
            )
            messages.success(request, 'Review submitted successfully.')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('products:detail', slug=product.slug)
