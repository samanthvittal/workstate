"""
WebSocket URL routing for time tracking.

Defines WebSocket URL patterns for timer real-time updates.
"""
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/timer/', consumers.TimerConsumer.as_asgi()),
]
