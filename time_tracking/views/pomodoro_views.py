"""
Pomodoro timer views for managing Pomodoro sessions and breaks.

Provides API endpoints for starting Pomodoro mode, completing sessions,
and managing break timers.
"""
import logging
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from time_tracking.models import PomodoroSession, TimeEntry, UserTimePreferences

logger = logging.getLogger(__name__)


class PomodoroStartView(LoginRequiredMixin, View):
    """
    Start a Pomodoro session for the active timer.

    Creates a PomodoroSession record linked to the current running timer.
    """

    def post(self, request):
        """
        Start a new Pomodoro session.

        Request body:
            - time_entry_id: ID of the running timer (optional, uses active timer if not provided)

        Returns:
            JSON response with Pomodoro session data
        """
        try:
            # Get the active timer
            active_timer = TimeEntry.objects.filter(
                user=request.user,
                is_running=True
            ).select_related('task', 'project').first()

            if not active_timer:
                return JsonResponse({
                    'error': 'No active timer found. Start a timer first.',
                }, status=400)

            # Get user's Pomodoro preferences
            try:
                prefs = request.user.time_preferences
                work_minutes = prefs.pomodoro_work_minutes
            except UserTimePreferences.DoesNotExist:
                work_minutes = 25  # Default

            # Get current session number
            existing_sessions = PomodoroSession.objects.filter(
                time_entry=active_timer
            ).count()
            session_number = existing_sessions + 1

            # Create Pomodoro session
            session = PomodoroSession.objects.create(
                time_entry=active_timer,
                session_number=session_number,
                started_at=timezone.now(),
                was_completed=False,
                break_taken=False,
            )

            logger.info(
                f"Started Pomodoro session #{session_number} for timer {active_timer.id}, "
                f"user {request.user.id}"
            )

            return JsonResponse({
                'success': True,
                'session': {
                    'id': session.id,
                    'session_number': session.session_number,
                    'started_at': session.started_at.isoformat(),
                    'work_minutes': work_minutes,
                    'time_entry_id': active_timer.id,
                    'task_title': active_timer.task.title,
                },
            }, status=201)

        except Exception as e:
            logger.error(f"Error starting Pomodoro session: {e}")
            return JsonResponse({
                'error': 'Failed to start Pomodoro session. Please try again.',
            }, status=500)


class PomodoroCompleteView(LoginRequiredMixin, View):
    """
    Mark a Pomodoro session as completed.

    Called when the work interval (default 25 minutes) finishes.
    """

    def post(self, request, session_id):
        """
        Complete a Pomodoro session.

        URL params:
            - session_id: ID of the Pomodoro session

        Returns:
            JSON response with updated session data
        """
        try:
            # Get the session
            session = PomodoroSession.objects.select_related(
                'time_entry', 'time_entry__task'
            ).get(
                id=session_id,
                time_entry__user=request.user
            )

            # Mark as completed
            session.complete_session()

            # Get break duration from preferences
            try:
                prefs = request.user.time_preferences
                break_minutes = prefs.pomodoro_break_minutes
            except UserTimePreferences.DoesNotExist:
                break_minutes = 5  # Default

            logger.info(
                f"Completed Pomodoro session #{session.session_number} "
                f"for user {request.user.id}"
            )

            return JsonResponse({
                'success': True,
                'session': {
                    'id': session.id,
                    'session_number': session.session_number,
                    'completed_at': session.completed_at.isoformat(),
                    'was_completed': session.was_completed,
                    'break_minutes': break_minutes,
                },
            })

        except PomodoroSession.DoesNotExist:
            return JsonResponse({
                'error': 'Pomodoro session not found.',
            }, status=404)
        except Exception as e:
            logger.error(f"Error completing Pomodoro session: {e}")
            return JsonResponse({
                'error': 'Failed to complete Pomodoro session. Please try again.',
            }, status=500)


class PomodoroBreakTakenView(LoginRequiredMixin, View):
    """
    Mark that a break was taken after a Pomodoro session.
    """

    def post(self, request, session_id):
        """
        Mark break as taken for a Pomodoro session.

        URL params:
            - session_id: ID of the Pomodoro session

        Returns:
            JSON response confirming break was marked
        """
        try:
            session = PomodoroSession.objects.get(
                id=session_id,
                time_entry__user=request.user
            )

            session.mark_break_taken()

            logger.info(
                f"Marked break taken for Pomodoro session #{session.session_number}, "
                f"user {request.user.id}"
            )

            return JsonResponse({
                'success': True,
                'session': {
                    'id': session.id,
                    'break_taken': session.break_taken,
                },
            })

        except PomodoroSession.DoesNotExist:
            return JsonResponse({
                'error': 'Pomodoro session not found.',
            }, status=404)
        except Exception as e:
            logger.error(f"Error marking break taken: {e}")
            return JsonResponse({
                'error': 'Failed to mark break. Please try again.',
            }, status=500)


class PomodoroStatusView(LoginRequiredMixin, View):
    """
    Get current Pomodoro status for the active timer.
    """

    def get(self, request):
        """
        Get Pomodoro status for active timer.

        Returns:
            JSON response with current Pomodoro session data (if any)
        """
        try:
            # Get active timer
            active_timer = TimeEntry.objects.filter(
                user=request.user,
                is_running=True
            ).first()

            if not active_timer:
                return JsonResponse({
                    'has_active_timer': False,
                    'pomodoro_active': False,
                })

            # Get current Pomodoro session
            current_session = PomodoroSession.objects.filter(
                time_entry=active_timer,
                was_completed=False
            ).order_by('-started_at').first()

            if not current_session:
                # Check if there are any completed sessions
                completed_count = PomodoroSession.objects.filter(
                    time_entry=active_timer,
                    was_completed=True
                ).count()

                return JsonResponse({
                    'has_active_timer': True,
                    'pomodoro_active': False,
                    'completed_sessions': completed_count,
                })

            # Get preferences
            try:
                prefs = request.user.time_preferences
                work_minutes = prefs.pomodoro_work_minutes
                break_minutes = prefs.pomodoro_break_minutes
            except UserTimePreferences.DoesNotExist:
                work_minutes = 25
                break_minutes = 5

            # Calculate elapsed time in current session
            elapsed_seconds = (timezone.now() - current_session.started_at).total_seconds()

            return JsonResponse({
                'has_active_timer': True,
                'pomodoro_active': True,
                'session': {
                    'id': current_session.id,
                    'session_number': current_session.session_number,
                    'started_at': current_session.started_at.isoformat(),
                    'elapsed_seconds': int(elapsed_seconds),
                    'work_minutes': work_minutes,
                    'break_minutes': break_minutes,
                    'was_completed': current_session.was_completed,
                    'break_taken': current_session.break_taken,
                },
            })

        except Exception as e:
            logger.error(f"Error getting Pomodoro status: {e}")
            return JsonResponse({
                'error': 'Failed to get Pomodoro status.',
            }, status=500)
