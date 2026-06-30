from django.views.generic import ListView
from django.db.models import Q
from apps.products.models import Product, Category, Brand

class SearchView(ListView):
    model = Product
    template_name = 'search/results.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        queryset = Product.objects.filter(status='APPROVED')

        if query:
            # Check if using PostgreSQL for SearchVector/Trigram or fall back to icontains for SQLite
            from django.conf import settings
            db_engine = settings.DATABASES['default']['ENGINE']
            if 'postgresql' in db_engine:
                from django.contrib.postgres.search import SearchVector, SearchRank, SearchQuery
                vector = SearchVector('title', weight='A') + SearchVector('description', weight='B')
                search_query = SearchQuery(query)
                queryset = queryset.annotate(rank=SearchRank(vector, search_query)).filter(rank__gte=0.1).order_by('-rank')
            else:
                queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))

        # Apply Filters
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        brand_slug = self.request.GET.get('brand')
        if brand_slug:
            queryset = queryset.filter(brand__slug=brand_slug)

        min_price = self.request.GET.get('min_price')
        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)

        max_price = self.request.GET.get('max_price')
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)

        rating = self.request.GET.get('rating')
        if rating:
            queryset = queryset.filter(average_rating__gte=rating)

        # Apply Sorting
        sort_by = self.request.GET.get('sort', 'newest')
        if sort_by == 'price_low_high':
            queryset = queryset.order_by('base_price')
        elif sort_by == 'price_high_low':
            queryset = queryset.order_by('-base_price')
        elif sort_by == 'popular':
            queryset = queryset.order_by('-sales_count')
        elif sort_by == 'rating':
            queryset = queryset.order_by('-average_rating')
        else: # default/newest
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['categories'] = Category.objects.filter(is_active=True, parent=None)
        context['brands'] = Brand.objects.filter(is_active=True)
        return context
