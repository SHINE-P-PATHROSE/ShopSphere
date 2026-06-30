from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/orders/(?P<order_number>\w+)/$', consumers.OrderStatusConsumer.as_asgi()),
]
