from django.contrib import admin
from .models import CMSPage, Banner


@admin.register(CMSPage)
class CMSPageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_published']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'position', 'is_active', 'order']
