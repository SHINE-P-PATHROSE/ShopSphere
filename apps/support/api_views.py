"""Support ticket API and views."""
from rest_framework import generics, permissions, serializers

from .models import SupportTicket, TicketMessage


class TicketMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)

    class Meta:
        model = TicketMessage
        fields = ['id', 'sender', 'sender_name', 'body', 'is_staff_reply', 'created_at']
        read_only_fields = ['sender', 'is_staff_reply']


class SupportTicketSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = ['id', 'subject', 'category', 'priority', 'status', 'order',
                  'messages', 'created_at']
        read_only_fields = ['status']


class TicketListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return SupportTicket.objects.none()
        return SupportTicket.objects.filter(user=self.request.user).prefetch_related('messages')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TicketDetailAPIView(generics.RetrieveAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = SupportTicket.objects.prefetch_related('messages')
        if self.request.user.role != 'ADMIN':
            qs = qs.filter(user=self.request.user)
        return qs
