"""Accounts API Serializers."""
import uuid
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Address, CustomerProfile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords don't match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data, role='CUSTOMER')


class EmailVerifySerializer(serializers.Serializer):
    """Accepts the UUID token from the verification email link."""
    token = serializers.UUIDField()


class ResendVerificationSerializer(serializers.Serializer):
    """Accepts an email address to resend a verification email."""
    email = serializers.EmailField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'role', 'avatar', 'is_verified', 'date_joined']
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'date_joined']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ['user']
