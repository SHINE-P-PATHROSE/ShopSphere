"""Auto-create store when vendor is approved."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import VendorProfile, Store


@receiver(post_save, sender=VendorProfile)
def create_store_on_approval(sender, instance, created, **kwargs):
    if instance.status == 'APPROVED':
        try:
            # Store already exists — nothing to do
            _ = instance.store
        except Store.DoesNotExist:
            slug = slugify(instance.business_name)
            counter = 1
            original = slug
            while Store.objects.filter(slug=slug).exists():
                slug = f'{original}-{counter}'
                counter += 1
            Store.objects.create(
                vendor=instance,
                name=instance.business_name,
                slug=slug,
            )
