from django.views.generic import TemplateView
from apps.products.models import Product, Category, Brand
from apps.cms.models import Banner

class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # We will add basic context here
        context['featured_products'] = Product.objects.filter(status='APPROVED', is_featured=True)[:8]
        context['latest_products'] = Product.objects.filter(status='APPROVED').order_by('-created_at')[:8]
        context['categories'] = Category.objects.filter(parent=None, is_active=True)[:10]
        context['banners'] = Banner.objects.filter(is_active=True, position='HOME_HERO')[:5]
        return context
