"""
Time suggestion API views for providing duration suggestions.

Provides endpoints for fetching time suggestions based on historical data.
"""
import logging
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from tasks.models import Task
from time_tracking.services.suggestions import TimeSuggestion

logger = logging.getLogger(__name__)


class TimeSuggestionAPIView(LoginRequiredMixin, View):
    """
    API endpoint to get time duration suggestion for a task.
    """

    def get(self, request, task_id):
        """
        Get time suggestion for a task.

        URL params:
            - task_id: ID of the task

        Query params (optional):
            - time_of_day: morning/afternoon/evening

        Returns:
            JSON response with suggestion data
        """
        try:
            # Get task and verify user has access
            task = get_object_or_404(
                Task.objects.select_related('task_list__workspace'),
                id=task_id,
                task_list__workspace__owner=request.user
            )

            # Get context from query params
            context = {}
            time_of_day = request.GET.get('time_of_day')
            if time_of_day:
                context['time_of_day'] = time_of_day

            # Get suggestion
            suggestion = TimeSuggestion.get_suggestion(
                user=request.user,
                task=task,
                context=context
            )

            if not suggestion:
                return JsonResponse({
                    'suggestion': None,
                    'message': 'Insufficient historical data for suggestion.',
                })

            # Format suggestion for display
            suggestion_text = TimeSuggestion.format_suggestion(suggestion)

            # Format duration for input field (HH:MM)
            duration = suggestion['duration']
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            duration_input = f"{hours}:{minutes:02d}"

            return JsonResponse({
                'suggestion': True,
                'suggestion_text': suggestion_text,
                'duration': str(duration),
                'duration_input': duration_input,
                'hours': hours,
                'minutes': minutes,
                'count': suggestion['count'],
                'method': suggestion['method'],
            })

        except Exception as e:
            logger.error(f"Error getting time suggestion: {e}")
            return JsonResponse({
                'error': 'Failed to get time suggestion.',
            }, status=500)
