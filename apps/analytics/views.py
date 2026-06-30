"""Analytics web views — admin and vendor dashboards."""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView

from .services import AnalyticsService


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Full platform analytics dashboard — admin only."""
    template_name = 'analytics/admin_dashboard.html'

    def test_func(self):
        return self.request.user.role == 'ADMIN'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        days = int(self.request.GET.get('days', 30))
        ctx['analytics'] = AnalyticsService.admin_dashboard(days)
        ctx['days'] = days
        return ctx


class VendorAnalyticsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Store-level analytics for approved vendors."""
    template_name = 'analytics/vendor_dashboard.html'

    def test_func(self):
        return (
            self.request.user.role == 'VENDOR'
            and hasattr(self.request.user, 'vendor_profile')
            and self.request.user.vendor_profile.status == 'APPROVED'
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        days = int(self.request.GET.get('days', 30))
        store = self.request.user.vendor_profile.store
        ctx['analytics'] = AnalyticsService.vendor_dashboard(store, days)
        ctx['days'] = days
        return ctx
