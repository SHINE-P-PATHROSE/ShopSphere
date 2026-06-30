from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import (
    Category, Brand, Tag, ProductAttribute, ProductAttributeValue,
    Product, ProductVariant, ProductImage,
)


@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_featured', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Tag)
admin.site.register(ProductAttribute)
admin.site.register(ProductAttributeValue)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'store', 'category', 'status', 'base_price', 'is_featured']
    list_filter = ['status', 'is_featured', 'category']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductVariantInline, ProductImageInline]
    actions = ['approve_products', 'reject_products']

    @admin.action(description='Approve selected products')
    def approve_products(self, request, queryset):
        queryset.update(status='APPROVED')

    @admin.action(description='Reject selected products')
    def reject_products(self, request, queryset):
        queryset.update(status='REJECTED')
