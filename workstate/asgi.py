"""
ASGI config for workstate project.

Exposes the ASGI callable as a module-level variable named 'application'.
Supports both HTTP and WebSocket connections via Django Channels.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workstate.settings')

# Initialize Django ASGI application early to ensure Django setup is complete
django_asgi_app = get_asgi_application()

# Import routing after Django initialization
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from time_tracking.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
