from rest_framework import serializers
from .models import VendorProfile, Store, StorePolicy

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'

class VendorProfileSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)

    class Meta:
        model = VendorProfile
        fields = '__all__'
        read_only_fields = ['user', 'status', 'approved_at', 'rejection_reason']
