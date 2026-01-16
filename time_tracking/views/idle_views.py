"""
Views for idle time notification actions.

Handles user actions on idle timer notifications: keep, discard, stop.
"""
import logging
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from time_tracking.models import IdleTimeNotification, TimeEntry
from time_tracking.services.cache import TimeEntryCache

logger = logging.getLogger(__name__)


class IdleKeepView(LoginRequiredMixin, View):
    """
    Handle 'keep time' action for idle notifications.

    Marks the notification as handled without making changes to the timer.
    """

    def post(self, request):
        """
        Process keep time action.

        Expected POST data:
        - notification_id: ID of the idle notification

        Returns:
            JsonResponse: Success or error message
        """
        try:
            notification_id = request.POST.get('notification_id')

            if not notification_id:
                return JsonResponse({
                    'error': 'Notification ID is required.'
                }, status=400)

            # Get notification and verify ownership
            try:
                notification = IdleTimeNotification.objects.select_related(
                    'time_entry'
                ).get(
                    id=notification_id,
                    user=request.user
                )
            except IdleTimeNotification.DoesNotExist:
                return JsonResponse({
                    'error': 'Notification not found or you do not have permission to access it.'
                }, status=404)

            # Check if already actioned
            if notification.action_taken != 'none':
                return JsonResponse({
                    'error': 'This notification has already been acted upon.'
                }, status=400)

            # Mark notification as handled
            notification.mark_action('keep')

            logger.info(f"User {request.user.email} kept idle time for timer {notification.time_entry.id}")

            return JsonResponse({
                'success': True,
                'message': 'Time kept successfully.',
                'notification_id': notification.id,
                'action': 'keep'
            })

        except Exception as e:
            logger.error(f"Error in idle keep action: {e}")
            return JsonResponse({
                'error': 'An error occurred while processing your request.'
            }, status=500)


class IdleDiscardView(LoginRequiredMixin, View):
    """
    Handle 'discard idle time' action for idle notifications.

    Adjusts the timer's duration by removing the idle time period.
    """

    def post(self, request):
        """
        Process discard idle time action.

        Expected POST data:
        - notification_id: ID of the idle notification

        Returns:
            JsonResponse: Success or error message
        """
        try:
            notification_id = request.POST.get('notification_id')

            if not notification_id:
                return JsonResponse({
                    'error': 'Notification ID is required.'
                }, status=400)

            # Get notification and verify ownership
            try:
                notification = IdleTimeNotification.objects.select_related(
                    'time_entry', 'time_entry__task'
                ).get(
                    id=notification_id,
                    user=request.user
                )
            except IdleTimeNotification.DoesNotExist:
                return JsonResponse({
                    'error': 'Notification not found or you do not have permission to access it.'
                }, status=404)

            # Check if already actioned
            if notification.action_taken != 'none':
                return JsonResponse({
                    'error': 'This notification has already been acted upon.'
                }, status=400)

            # Get the time entry
            time_entry = notification.time_entry

            # Check if timer is still running
            if not time_entry.is_running:
                return JsonResponse({
                    'error': 'Timer is no longer running.'
                }, status=400)

            # Calculate new end time (set to idle_start_time)
            # This effectively removes the idle time from the timer
            time_entry.end_time = notification.idle_start_time
            time_entry.is_running = False

            # Calculate new duration
            if time_entry.start_time:
                time_entry.duration = notification.idle_start_time - time_entry.start_time
            else:
                time_entry.duration = timezone.timedelta(0)

            # Save the updated time entry
            time_entry.save(update_fields=['end_time', 'is_running', 'duration', 'updated_at'])

            # Clear from cache
            TimeEntryCache.clear_active_timer(request.user.id)

            # Mark notification as handled
            notification.mark_action('discard')

            logger.info(f"User {request.user.email} discarded idle time for timer {time_entry.id}")

            return JsonResponse({
                'success': True,
                'message': 'Idle time discarded successfully.',
                'notification_id': notification.id,
                'action': 'discard',
                'time_entry_id': time_entry.id,
                'new_duration_seconds': int(time_entry.duration.total_seconds())
            })

        except Exception as e:
            logger.error(f"Error in idle discard action: {e}")
            return JsonResponse({
                'error': 'An error occurred while processing your request.'
            }, status=500)


class IdleStopView(LoginRequiredMixin, View):
    """
    Handle 'stop timer at idle start' action for idle notifications.

    Stops the timer and sets end_time to when idle period started.
    """

    def post(self, request):
        """
        Process stop at idle start action.

        Expected POST data:
        - notification_id: ID of the idle notification

        Returns:
            JsonResponse: Success or error message
        """
        try:
            notification_id = request.POST.get('notification_id')

            if not notification_id:
                return JsonResponse({
                    'error': 'Notification ID is required.'
                }, status=400)

            # Get notification and verify ownership
            try:
                notification = IdleTimeNotification.objects.select_related(
                    'time_entry', 'time_entry__task'
                ).get(
                    id=notification_id,
                    user=request.user
                )
            except IdleTimeNotification.DoesNotExist:
                return JsonResponse({
                    'error': 'Notification not found or you do not have permission to access it.'
                }, status=404)

            # Check if already actioned
            if notification.action_taken != 'none':
                return JsonResponse({
                    'error': 'This notification has already been acted upon.'
                }, status=400)

            # Get the time entry
            time_entry = notification.time_entry

            # Check if timer is still running
            if not time_entry.is_running:
                return JsonResponse({
                    'error': 'Timer is no longer running.'
                }, status=400)

            # Stop timer at idle_start_time
            time_entry.end_time = notification.idle_start_time
            time_entry.is_running = False

            # Calculate final duration
            if time_entry.start_time:
                time_entry.duration = notification.idle_start_time - time_entry.start_time
            else:
                time_entry.duration = timezone.timedelta(0)

            # Apply time rounding if configured
            try:
                from time_tracking.models import UserTimePreferences
                preferences = UserTimePreferences.objects.get(user=request.user)
                if preferences.rounding_interval > 0:
                    time_entry.duration = time_entry.apply_rounding(
                        preferences.rounding_interval,
                        preferences.rounding_method
                    )
            except UserTimePreferences.DoesNotExist:
                pass

            # Save the updated time entry
            time_entry.save(update_fields=['end_time', 'is_running', 'duration', 'updated_at'])

            # Clear from cache
            TimeEntryCache.clear_active_timer(request.user.id)

            # Mark notification as handled
            notification.mark_action('stop_at_idle')

            logger.info(f"User {request.user.email} stopped timer {time_entry.id} at idle start")

            return JsonResponse({
                'success': True,
                'message': 'Timer stopped at idle start successfully.',
                'notification_id': notification.id,
                'action': 'stop_at_idle',
                'time_entry_id': time_entry.id,
                'duration_seconds': int(time_entry.duration.total_seconds())
            })

        except Exception as e:
            logger.error(f"Error in idle stop action: {e}")
            return JsonResponse({
                'error': 'An error occurred while processing your request.'
            }, status=500)


class IdleNotificationListView(LoginRequiredMixin, View):
    """
    Get list of pending idle notifications for current user.

    Used by frontend to poll for new idle notifications.
    """

    def get(self, request):
        """
        Return list of pending idle notifications.

        Returns:
            JsonResponse: List of pending notifications
        """
        try:
            # Get all pending notifications for user
            notifications = IdleTimeNotification.objects.select_related(
                'time_entry', 'time_entry__task', 'time_entry__project'
            ).filter(
                user=request.user,
                action_taken='none',
                time_entry__is_running=True
            ).order_by('-created_at')

            notification_list = []
            for notif in notifications:
                notification_list.append({
                    'id': notif.id,
                    'time_entry_id': notif.time_entry.id,
                    'task_name': notif.time_entry.task.title if notif.time_entry.task else 'Unknown',
                    'project_name': notif.time_entry.project.name if notif.time_entry.project else '',
                    'idle_start_time': notif.idle_start_time.isoformat(),
                    'notification_sent_at': notif.notification_sent_at.isoformat(),
                    'timer_start_time': notif.time_entry.start_time.isoformat() if notif.time_entry.start_time else None,
                })

            return JsonResponse({
                'notifications': notification_list,
                'count': len(notification_list)
            })

        except Exception as e:
            logger.error(f"Error fetching idle notifications: {e}")
            return JsonResponse({
                'error': 'An error occurred while fetching notifications.'
            }, status=500)
