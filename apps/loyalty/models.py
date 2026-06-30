"""Loyalty Models."""
import shortuuid
from django.db import models
from apps.core.models import TimeStampedModel


def _default_referral_code():
    return shortuuid.ShortUUID().random(length=8).upper()


class LoyaltyAccount(TimeStampedModel):
    TIER_CHOICES = [('BRONZE','Bronze'),('SILVER','Silver'),('GOLD','Gold'),('PLATINUM','Platinum')]

    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='loyalty_account')
    points = models.PositiveIntegerField(default=0)
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='BRONZE')
    referral_code = models.CharField(max_length=20, unique=True, default=_default_referral_code)
    total_earned = models.PositiveIntegerField(default=0)
    total_redeemed = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.email} - {self.tier} ({self.points} pts)"


class PointTransaction(TimeStampedModel):
    TYPE_CHOICES = [('EARNED','Earned'),('REDEEMED','Redeemed'),('EXPIRED','Expired'),('REFERRAL','Referral Bonus'),('CASHBACK','Cashback')]

    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='transactions')
    points = models.IntegerField()
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.CharField(max_length=200)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)


class Referral(TimeStampedModel):
    referrer = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='referrals_made')
    referred_user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='referred_by')
    reward_given = models.BooleanField(default=False)
    reward_points = models.PositiveIntegerField(default=100)
