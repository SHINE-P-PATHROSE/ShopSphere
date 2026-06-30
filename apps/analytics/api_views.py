"""Analytics API and dashboard views."""
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdmin, IsVendor
from .services import AnalyticsService


class AdminAnalyticsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        return Response(AnalyticsService.admin_dashboard(days))


class VendorAnalyticsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def get(self, request):
        store = request.user.vendor_profile.store
        days = int(request.query_params.get('days', 30))
        return Response(AnalyticsService.vendor_dashboard(store, days))
