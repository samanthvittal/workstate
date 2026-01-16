"""
WebSocket consumer for real-time timer updates.

Handles WebSocket connections for timer updates, enabling cross-tab
synchronization and real-time notifications.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class TimerConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for timer updates.

    Manages personal timer channel groups for each user, broadcasting
    timer events (started, stopped, updated, discarded) to all connected
    tabs for cross-tab synchronization.
    """

    async def connect(self):
        """
        Handle WebSocket connection.

        Authenticates user and adds them to their personal timer channel group.
        Rejects unauthenticated connections.
        """
        self.user = self.scope.get('user')

        # Reject unauthenticated users
        if not self.user or isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            logger.warning("WebSocket connection rejected: unauthenticated user")
            await self.close(code=4001)
            return

        # Create personal channel group name
        self.timer_group_name = f"timer_{self.user.id}"

        try:
            # Add this connection to user's timer channel group
            await self.channel_layer.group_add(
                self.timer_group_name,
                self.channel_name
            )

            # Accept connection
            await self.accept()

            logger.info(f"WebSocket connected: user {self.user.id}, channel {self.channel_name}")
        except Exception as e:
            logger.error(f"WebSocket connection failed (Redis unavailable?): {e}")
            # Accept connection anyway - WebSocket will work without cross-tab sync
            await self.accept()
            logger.warning(f"WebSocket connected without channel layer (degraded mode): user {self.user.id}")

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.

        Removes user from their timer channel group.

        Args:
            close_code: WebSocket close code
        """
        # Only remove from group if user was authenticated
        if hasattr(self, 'timer_group_name'):
            try:
                await self.channel_layer.group_discard(
                    self.timer_group_name,
                    self.channel_name
                )
                logger.info(f"WebSocket disconnected: user {self.user.id}, code {close_code}")
            except Exception as e:
                logger.error(f"WebSocket disconnect error (Redis unavailable?): {e}")
                # Continue anyway - connection is closing

    async def receive(self, text_data):
        """
        Handle messages received from WebSocket.

        Currently not used - all timer actions go through HTTP API.
        Reserved for future client-initiated actions if needed.

        Args:
            text_data: JSON string from client
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            logger.debug(f"Received WebSocket message: {message_type} from user {self.user.id}")

            # Future: handle client-initiated actions here if needed
            # For now, all actions go through HTTP API which broadcasts via group_send

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON received from WebSocket: {e}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}", exc_info=True)

    async def timer_started(self, event):
        """
        Handle timer started event broadcast.

        Sends timer_started message to WebSocket client with full timer data.

        Args:
            event: Event dict with timer_data
        """
        await self.send(text_data=json.dumps({
            'type': 'timer.started',
            'data': event.get('timer_data', {})
        }))
        logger.debug(f"Sent timer.started to user {self.user.id}")

    async def timer_stopped(self, event):
        """
        Handle timer stopped event broadcast.

        Sends timer_stopped message to WebSocket client with final timer data.

        Args:
            event: Event dict with timer_data
        """
        await self.send(text_data=json.dumps({
            'type': 'timer.stopped',
            'data': event.get('timer_data', {})
        }))
        logger.debug(f"Sent timer.stopped to user {self.user.id}")

    async def timer_updated(self, event):
        """
        Handle timer updated event broadcast.

        Sends timer_updated message to WebSocket client with updated timer data.
        Used when timer description or other fields are modified.

        Args:
            event: Event dict with timer_data
        """
        await self.send(text_data=json.dumps({
            'type': 'timer.updated',
            'data': event.get('timer_data', {})
        }))
        logger.debug(f"Sent timer.updated to user {self.user.id}")

    async def timer_discarded(self, event):
        """
        Handle timer discarded event broadcast.

        Sends timer_discarded message to WebSocket client.

        Args:
            event: Event dict with timer_id
        """
        await self.send(text_data=json.dumps({
            'type': 'timer.discarded',
            'data': {
                'timer_id': event.get('timer_id')
            }
        }))
        logger.debug(f"Sent timer.discarded to user {self.user.id}")
