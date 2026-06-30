"""Loyalty program views."""
import shortuuid
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum

from .models import LoyaltyAccount, PointTransaction


class LoyaltyDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'loyalty/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        account, _ = LoyaltyAccount.objects.get_or_create(
            user=self.request.user,
            defaults={'referral_code': shortuuid.ShortUUID().random(length=8).upper()},
        )
        ctx['account'] = account
        ctx['transactions'] = PointTransaction.objects.filter(account=account)[:20]
        return ctx
