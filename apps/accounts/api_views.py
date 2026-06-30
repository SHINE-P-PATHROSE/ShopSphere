"""Accounts API Views."""
from rest_framework import generics, permissions, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    RegisterSerializer, UserSerializer, AddressSerializer,
    EmailVerifySerializer, ResendVerificationSerializer,
)
from .models import Address
from .services import AccountService
from .tasks import send_verification_email_task


class RegisterAPIView(generics.CreateAPIView):
    """Register a new customer account and send a verification email."""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        send_verification_email_task.delay(user.id)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = {
            'detail': 'Registration successful. Please check your email to verify your account.',
            'email': response.data.get('email'),
        }
        return response


class VerifiedTokenObtainPairView(TokenObtainPairView):
    """JWT login — blocks unverified users before issuing tokens."""

    def post(self, request, *args, **kwargs):
        # Run the parent serializer to validate credentials first
        serializer = TokenObtainPairSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.user

        if not user.is_verified:
            raise AuthenticationFailed(
                'Email address is not verified. '
                'Please check your inbox or request a new verification email.'
            )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class VerifyEmailAPIView(APIView):
    """Verify a user's email address using the UUID token from the link."""
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailVerifySerializer  # used by drf-spectacular

    def post(self, request):
        serializer = EmailVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        success, message = AccountService.verify_email(serializer.validated_data['token'])
        if success:
            return Response({'detail': message}, status=status.HTTP_200_OK)
        return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailAPIView(APIView):
    """Resend the verification email for an unverified account."""
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'resend_verification'
    serializer_class = ResendVerificationSerializer  # used by drf-spectacular

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Always return 200 — never reveal whether the email exists
        from .models import User
        try:
            user = User.objects.get(email=serializer.validated_data['email'])
            if not user.is_verified:
                send_verification_email_task.delay(user.id)
        except User.DoesNotExist:
            pass
        return Response(
            {'detail': 'If that account exists and is unverified, a new email has been sent.'},
            status=status.HTTP_200_OK,
        )


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AddressListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Address.objects.none()
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Address.objects.none()
        return Address.objects.filter(user=self.request.user)
