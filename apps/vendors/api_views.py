from rest_framework import generics, permissions
from .models import VendorProfile, Store
from .serializers import VendorProfileSerializer, StoreSerializer

class VendorListAPIView(generics.ListAPIView):
    queryset = VendorProfile.objects.filter(status='APPROVED')
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.AllowAny]

class VendorDetailAPIView(generics.RetrieveAPIView):
    queryset = VendorProfile.objects.all()
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.AllowAny]

class StoreAPIView(generics.RetrieveUpdateAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
