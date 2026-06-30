"""
Products Models - Complete product catalog with categories, brands, variants, and inventory.
"""
from django.db import models
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey
from apps.core.models import TimeStampedModel, SoftDeleteModel


class Category(MPTTModel, TimeStampedModel):
    """Hierarchical product categories using MPTT."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text='CSS icon class')
    image = models.ImageField(upload_to='categories/', blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class MPTTMeta:
        order_insertion_by = ['order', 'name']

    class Meta:
        verbose_name_plural = 'Categories'
        indexes = [models.Index(fields=['slug'])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Brand(TimeStampedModel):
    """Product brands."""
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    logo = models.ImageField(upload_to='brands/', blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    """Product tags for search and filtering."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductAttribute(models.Model):
    """Product attributes like Size, Color, Material."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    """Values for product attributes (e.g., Size: S, M, L)."""
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=100)

    class Meta:
        unique_together = ['attribute', 'value']
        ordering = ['attribute', 'value']

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class Product(SoftDeleteModel):
    """Main product model - represents a product listing."""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    store = models.ForeignKey('vendors.Store', on_delete=models.CASCADE, related_name='products')
    category = TreeForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    title = models.CharField(max_length=300, db_index=True)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                         help_text='Original price for showing discount')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT', db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='products')
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True, max_length=500)
    views_count = models.PositiveIntegerField(default=0)
    sales_count = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text='Weight in grams')
    video_url = models.URLField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['store', 'status']),
            models.Index(fields=['-sales_count']),
            models.Index(fields=['-average_rating']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure uniqueness
            counter = 1
            original_slug = self.slug
            while Product.all_objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def discount_percentage(self):
        if self.compare_price and self.compare_price > self.base_price:
            return int(((self.compare_price - self.base_price) / self.compare_price) * 100)
        return 0

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

    @property
    def in_stock(self):
        return self.variants.filter(stock__gt=0, is_active=True).exists()

    @property
    def price_range(self):
        variants = self.variants.filter(is_active=True)
        if variants.exists():
            prices = variants.values_list('price', flat=True)
            min_p, max_p = min(prices), max(prices)
            if min_p == max_p:
                return f"₹{min_p}"
            return f"₹{min_p} - ₹{max_p}"
        return f"₹{self.base_price}"


class ProductVariant(TimeStampedModel):
    """Product variant with specific attribute combination (e.g., Size:M + Color:Red)."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=50, unique=True, verbose_name='SKU')
    attribute_values = models.ManyToManyField(ProductAttributeValue, blank=True, related_name='variants')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['price']
        indexes = [
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        attrs = ", ".join([str(av) for av in self.attribute_values.all()])
        return f"{self.product.title} [{attrs}]" if attrs else f"{self.product.title} [Default]"

    @property
    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold

    @property
    def is_in_stock(self):
        return self.stock > 0 and self.is_active


class ProductImage(TimeStampedModel):
    """Product images with ordering."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/%Y/%m/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', '-is_primary']

    def __str__(self):
        return f"Image for {self.product.title}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
