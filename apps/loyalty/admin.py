from django.contrib import admin
from .models import LoyaltyAccount, PointTransaction, Referral


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'tier', 'points', 'referral_code']


admin.site.register(PointTransaction)
admin.site.register(Referral)
