"""Notification service layer."""
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Notification


class NotificationService:
    """Create in-app notifications and push via WebSocket."""

    @staticmethod
    def create(user, title, message, notification_type='SYSTEM', link=''):
        notif = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
        )
        NotificationService._push_ws(user.id, {
            'id': notif.id,
            'title': title,
            'message': message,
            'type': notification_type,
            'link': link,
        })
        return notif

    @staticmethod
    def _push_ws(user_id, payload):
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'user_{user_id}',
                {'type': 'notification.message', 'data': payload},
            )

    @staticmethod
    def notify_order_created(user, order):
        NotificationService.create(
            user,
            'Order Placed',
            f'Your order #{order.order_number} has been placed successfully.',
            'ORDER',
            f'/orders/{order.order_number}/',
        )

    @staticmethod
    def notify_order_status(user, order, status):
        NotificationService.create(
            user,
            'Order Update',
            f'Order #{order.order_number} is now {status.replace("_", " ").title()}.',
            'ORDER',
            f'/orders/{order.order_number}/',
        )
