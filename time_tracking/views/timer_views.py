"""
Timer API views for starting, stopping, and managing timers.

Provides JSON API endpoints for timer operations with proper authorization,
validation, error handling, and WebSocket broadcasting for real-time updates.
"""
import json
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from tasks.models import Task
from time_tracking.models import TimeEntry, UserTimePreferences
from time_tracking.services.cache import TimeEntryCache
from time_tracking.serializers import TimeEntrySerializer

logger = logging.getLogger(__name__)


class TimerAPIView(LoginRequiredMixin, View):
    """
    Base view for timer API endpoints.

    Provides common functionality for authentication, JSON parsing,
    error handling, and WebSocket broadcasting.
    """

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to handle JSON responses for unauthenticated users."""
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Authentication required.'
            }, status=401)
        return super().dispatch(request, *args, **kwargs)

    def parse_json_body(self, request):
        """
        Parse JSON request body.

        Args:
            request: HTTP request

        Returns:
            dict: Parsed JSON data

        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            if request.body:
                return json.loads(request.body)
            return {}
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in request: {e}")
            raise ValueError("Invalid JSON in request body.")

    def error_response(self, message, status=400, field=None):
        """
        Generate error response.

        Args:
            message: Error message
            status: HTTP status code
            field: Optional field name for validation errors

        Returns:
            JsonResponse: Error response
        """
        data = {'error': message}
        if field:
            data['field'] = field
        return JsonResponse(data, status=status)

    def success_response(self, data, status=200):
        """
        Generate success response.

        Args:
            data: Response data
            status: HTTP status code

        Returns:
            JsonResponse: Success response
        """
        return JsonResponse(data, status=status)

    def broadcast_timer_event(self, user_id, event_type, data):
        """
        Broadcast timer event via WebSocket.

        Args:
            user_id: User ID
            event_type: Event type (timer_started, timer_stopped, timer_updated, timer_discarded)
            data: Event data
        """
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"timer_{user_id}",
                    {
                        'type': event_type,
                        **data
                    }
                )
                logger.debug(f"Broadcast {event_type} to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast WebSocket message: {e}", exc_info=True)


class TimerStartView(TimerAPIView):
    """
    Start timer endpoint.

    POST /api/timers/start/
    Body: {task_id, description (optional), auto_stop_current (optional)}

    Validates task access, checks for active timer, starts new timer,
    and broadcasts timer_started event via WebSocket.
    """

    def post(self, request):
        """Handle timer start request."""
        try:
            # Parse request data
            data = self.parse_json_body(request)
            task_id = data.get('task_id')
            description = data.get('description', '').strip()
            auto_stop_current = data.get('auto_stop_current', False)

            # Validate task_id provided
            if not task_id:
                return self.error_response(
                    'Task ID is required.',
                    field='task_id'
                )

            # Validate task exists and user has access
            try:
                task = Task.objects.select_related('task_list', 'task_list__workspace').get(
                    id=task_id
                )
            except Task.DoesNotExist:
                return self.error_response(
                    'Task not found.',
                    status=404,
                    field='task_id'
                )

            # Check user has access to task (via workspace ownership)
            if task.task_list.workspace.owner != request.user:
                return self.error_response(
                    'You do not have access to this task.',
                    status=403
                )

            # Check for existing active timer
            active_timer = TimeEntry.objects.select_related('task', 'project').filter(
                user=request.user,
                is_running=True
            ).first()

            # If active timer exists and auto-stop not confirmed, return confirmation dialog
            if active_timer and not auto_stop_current:
                confirmation_data = TimeEntrySerializer.serialize_confirmation_dialog(
                    active_timer,
                    task
                )
                return self.success_response(confirmation_data, status=200)

            # Start new timer (with transaction to ensure atomicity)
            with transaction.atomic():
                # Stop previous timer if exists
                if active_timer:
                    active_timer.stop()
                    TimeEntryCache.clear_active_timer(request.user.id)

                    # Broadcast timer_stopped event
                    stopped_timer_data = TimeEntrySerializer.serialize(active_timer)
                    self.broadcast_timer_event(
                        request.user.id,
                        'timer_stopped',
                        {'timer_data': stopped_timer_data}
                    )

                    logger.info(f"Auto-stopped timer {active_timer.id} for user {request.user.id}")

                # Create new timer
                time_entry = TimeEntry(
                    user=request.user,
                    task=task,
                    project=task.task_list,  # Inherit project from task
                    start_time=timezone.now(),
                    duration=timezone.timedelta(0),
                    description=description,
                    is_running=True,
                )
                time_entry.save()

                # Cache active timer
                TimeEntryCache.set_active_timer(request.user.id, time_entry)

                logger.info(f"Started timer {time_entry.id} for user {request.user.id} on task {task_id}")

                # Return timer data
                timer_data = TimeEntrySerializer.serialize(time_entry)

                # Broadcast timer_started event
                self.broadcast_timer_event(
                    request.user.id,
                    'timer_started',
                    {'timer_data': timer_data}
                )

                return self.success_response(timer_data, status=201)

        except ValueError as e:
            return self.error_response(str(e), status=400)
        except Exception as e:
            logger.error(f"Unexpected error starting timer: {e}", exc_info=True)
            return self.error_response(
                'An error occurred while starting the timer. Please try again.',
                status=500
            )


class TimerStopView(TimerAPIView):
    """
    Stop timer endpoint.

    POST /api/timers/stop/
    Body: {} (no parameters required)

    Stops the user's active timer, applies time rounding rules, saves to database,
    and broadcasts timer_stopped event via WebSocket.
    """

    def post(self, request):
        """Handle timer stop request."""
        try:
            # Check for active timer
            active_timer = TimeEntry.objects.select_related(
                'task',
                'project',
                'user__time_preferences'
            ).filter(
                user=request.user,
                is_running=True
            ).first()

            if not active_timer:
                return self.error_response(
                    'No active timer found.',
                    status=404
                )

            # Stop timer with transaction
            with transaction.atomic():
                # Calculate end time and duration
                end_time = timezone.now()

                # Calculate duration manually
                if active_timer.start_time:
                    duration = end_time - active_timer.start_time
                else:
                    duration = timezone.timedelta(0)

                # Apply time rounding rules from UserTimePreferences
                try:
                    preferences = request.user.time_preferences
                    if preferences.rounding_interval > 0:
                        rounded_duration = active_timer.apply_rounding(
                            preferences.rounding_interval,
                            preferences.rounding_method
                        )
                        # Ensure rounded duration is at least 1 second to pass validation
                        if rounded_duration <= timezone.timedelta(0):
                            rounded_duration = timezone.timedelta(seconds=1)
                        duration = rounded_duration
                except UserTimePreferences.DoesNotExist:
                    # No preferences set, use actual duration (no rounding)
                    pass

                # Update timer fields
                active_timer.end_time = end_time
                active_timer.is_running = False
                active_timer.duration = duration
                active_timer.save(update_fields=['end_time', 'is_running', 'duration', 'updated_at'])

                # Clear from cache
                TimeEntryCache.clear_active_timer(request.user.id)

                logger.info(f"Stopped timer {active_timer.id} for user {request.user.id}")

                # Return final time entry data
                timer_data = TimeEntrySerializer.serialize(active_timer)

                # Broadcast timer_stopped event
                self.broadcast_timer_event(
                    request.user.id,
                    'timer_stopped',
                    {'timer_data': timer_data}
                )

                return self.success_response(timer_data, status=200)

        except Exception as e:
            logger.error(f"Unexpected error stopping timer: {e}", exc_info=True)
            return self.error_response(
                'An error occurred while stopping the timer. Please try again.',
                status=500
            )


class TimerDiscardView(TimerAPIView):
    """
    Discard timer endpoint.

    DELETE /api/timers/discard/
    Body: {confirmed (optional)}

    Discards the user's active timer without creating a time entry record,
    and broadcasts timer_discarded event via WebSocket.
    """

    def post(self, request):
        """Handle timer discard request via POST with _method=DELETE."""
        try:
            # Parse request data
            data = self.parse_json_body(request)
            confirmed = data.get('confirmed', False)

            # Check for active timer
            active_timer = TimeEntry.objects.select_related('task', 'project').filter(
                user=request.user,
                is_running=True
            ).first()

            if not active_timer:
                return self.error_response(
                    'No active timer found.',
                    status=404
                )

            # If not confirmed, return confirmation dialog
            if not confirmed:
                confirmation_data = TimeEntrySerializer.serialize_discard_confirmation(
                    active_timer
                )
                return self.success_response(confirmation_data, status=200)

            # Discard timer with transaction
            with transaction.atomic():
                timer_id = active_timer.id
                active_timer.delete()

                # Clear from cache
                TimeEntryCache.clear_active_timer(request.user.id)

                logger.info(f"Discarded timer {timer_id} for user {request.user.id}")

                # Broadcast timer_discarded event
                self.broadcast_timer_event(
                    request.user.id,
                    'timer_discarded',
                    {'timer_id': timer_id}
                )

                # Return success message
                return self.success_response({
                    'message': 'Timer discarded successfully.',
                    'discarded_timer_id': timer_id
                }, status=200)

        except ValueError as e:
            return self.error_response(str(e), status=400)
        except Exception as e:
            logger.error(f"Unexpected error discarding timer: {e}", exc_info=True)
            return self.error_response(
                'An error occurred while discarding the timer. Please try again.',
                status=500
            )

    def delete(self, request):
        """Handle timer discard request via DELETE."""
        return self.post(request)


class TimerGetActiveView(TimerAPIView):
    """
    Get active timer endpoint.

    GET /api/timers/active/

    Returns the user's currently active timer, or 404 if no active timer.
    Used by header widget for initial load.
    """

    def get(self, request):
        """Handle get active timer request."""
        try:
            # Check Redis cache first, fallback to PostgreSQL
            cached_timer = TimeEntryCache.get_active_timer(request.user.id)

            if cached_timer:
                # Calculate fresh elapsed time
                from datetime import datetime
                if cached_timer.get('start_time'):
                    # Parse ISO format datetime string
                    start_time_str = cached_timer['start_time']
                    # Handle timezone-aware datetime strings
                    if start_time_str.endswith('Z'):
                        start_time_str = start_time_str.replace('Z', '+00:00')
                    start_time = datetime.fromisoformat(start_time_str)
                    elapsed = timezone.now() - start_time
                    cached_timer['elapsed_time'] = int(elapsed.total_seconds())

                return self.success_response(cached_timer, status=200)

            # No active timer found
            return self.error_response(
                'No active timer found.',
                status=404
            )

        except Exception as e:
            logger.error(f"Unexpected error getting active timer: {e}", exc_info=True)
            return self.error_response(
                'An error occurred while retrieving the active timer. Please try again.',
                status=500
            )
