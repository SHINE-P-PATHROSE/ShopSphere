"""CMS Models."""
from django.db import models
from apps.core.models import TimeStampedModel


class CMSPage(TimeStampedModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    meta_description = models.TextField(blank=True, max_length=300)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Banner(TimeStampedModel):
    POSITION_CHOICES = [('HOME_HERO','Home Hero'),('HOME_SIDE','Home Sidebar'),('CATEGORY','Category Page'),('PROMO','Promotional')]

    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='banners/')
    link = models.URLField(blank=True)
    position = models.CharField(max_length=15, choices=POSITION_CHOICES, default='HOME_HERO')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title
