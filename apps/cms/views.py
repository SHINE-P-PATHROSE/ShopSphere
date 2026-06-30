from django.views.generic import DetailView
from .models import CMSPage

class CMSPageDetailView(DetailView):
    model = CMSPage
    template_name = 'cms/page_detail.html'
    context_object_name = 'page'
    slug_field = 'slug'
