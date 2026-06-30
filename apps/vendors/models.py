"""
Vendors Models - VendorProfile, Store, StorePolicy.
"""
from django.db import models
from django.utils.text import slugify
from apps.core.models import TimeStampedModel


class VendorProfile(TimeStampedModel):
    """Vendor profile linked to a User with role=VENDOR."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended'),
    ]

    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='vendor_profile')
    business_name = models.CharField(max_length=200)
    business_email = models.EmailField()
    business_phone = models.CharField(max_length=15)
    gstin = models.CharField(max_length=15, blank=True, verbose_name='GSTIN')
    pan = models.CharField(max_length=10, blank=True, verbose_name='PAN')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00,
                                          help_text='Platform commission percentage')
    rejection_reason = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=20, blank=True)
    bank_ifsc = models.CharField(max_length=11, blank=True)
    id_proof = models.FileField(upload_to='vendors/documents/', blank=True)
    address_proof = models.FileField(upload_to='vendors/documents/', blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vendor Profile'

    def __str__(self):
        return f"{self.business_name} ({self.get_status_display()})"


class Store(TimeStampedModel):
    """Vendor's public store."""
    vendor = models.OneToOneField(VendorProfile, on_delete=models.CASCADE, related_name='store')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='stores/logos/', blank=True)
    banner = models.ImageField(upload_to='stores/banners/', blank=True)
    tagline = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    total_sales = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    class Meta:
        ordering = ['-total_sales']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class StorePolicy(TimeStampedModel):
    """Store-specific policies (returns, shipping, etc.)."""
    POLICY_TYPES = [
        ('RETURN', 'Return Policy'),
        ('SHIPPING', 'Shipping Policy'),
        ('PRIVACY', 'Privacy Policy'),
        ('TERMS', 'Terms & Conditions'),
    ]

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='policies')
    policy_type = models.CharField(max_length=10, choices=POLICY_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField()

    class Meta:
        unique_together = ['store', 'policy_type']
        verbose_name_plural = 'Store Policies'

    def __str__(self):
        return f"{self.store.name} - {self.get_policy_type_display()}"
