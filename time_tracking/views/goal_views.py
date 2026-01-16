"""
Time goal views for managing time budgets and tracking progress.

Provides endpoints for creating, updating, and viewing time goals.
"""
import logging
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404
from time_tracking.models import TimeGoal
from datetime import timedelta

logger = logging.getLogger(__name__)


class TimeGoalListView(LoginRequiredMixin, ListView):
    """
    List all active time goals for the user.
    """
    model = TimeGoal
    template_name = 'time_tracking/goals/goal_list.html'
    context_object_name = 'goals'
    paginate_by = 20

    def get_queryset(self):
        """Return only user's active goals."""
        return TimeGoal.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('project', 'task').order_by('-created_at')

    def get_context_data(self, **kwargs):
        """Add progress data for each goal."""
        context = super().get_context_data(**kwargs)

        # Add progress information to each goal
        goals_with_progress = []
        for goal in context['goals']:
            progress = goal.get_progress()
            percentage = goal.get_percentage_complete()

            # Determine warning level
            if percentage >= 120:
                warning_level = 'danger'
            elif percentage >= 100:
                warning_level = 'warning'
            elif percentage >= 80:
                warning_level = 'caution'
            else:
                warning_level = 'normal'

            goals_with_progress.append({
                'goal': goal,
                'progress': progress,
                'percentage': percentage,
                'warning_level': warning_level,
                'is_overbudget': goal.is_overbudget(),
            })

        context['goals_with_progress'] = goals_with_progress
        return context


class TimeGoalProgressAPIView(LoginRequiredMixin, View):
    """
    API endpoint to get progress for a specific time goal.
    """

    def get(self, request, goal_id):
        """
        Get goal progress.

        URL params:
            - goal_id: ID of the time goal

        Returns:
            JSON response with progress data
        """
        try:
            goal = get_object_or_404(
                TimeGoal,
                id=goal_id,
                user=request.user
            )

            progress = goal.get_progress()
            percentage = goal.get_percentage_complete()

            # Format durations for display
            progress_hours = progress.total_seconds() / 3600
            target_hours = goal.target_duration.total_seconds() / 3600
            remaining = goal.target_duration - progress

            return JsonResponse({
                'success': True,
                'goal': {
                    'id': goal.id,
                    'goal_type': goal.goal_type,
                    'target_duration': str(goal.target_duration),
                    'target_hours': round(target_hours, 2),
                    'progress': str(progress),
                    'progress_hours': round(progress_hours, 2),
                    'remaining': str(max(remaining, timedelta(0))),
                    'percentage': round(percentage, 1),
                    'is_overbudget': goal.is_overbudget(),
                    'project_id': goal.project_id,
                    'task_id': goal.task_id,
                },
            })

        except Exception as e:
            logger.error(f"Error getting goal progress: {e}")
            return JsonResponse({
                'error': 'Failed to get goal progress.',
            }, status=500)


class TimeGoalCreateAPIView(LoginRequiredMixin, View):
    """
    API endpoint to create a new time goal.
    """

    def post(self, request):
        """
        Create a new time goal.

        Request body:
            - goal_type: Type of goal (daily/weekly/monthly/total)
            - target_hours: Target duration in hours (decimal)
            - project_id: Project ID (optional, mutually exclusive with task_id)
            - task_id: Task ID (optional, mutually exclusive with project_id)
            - start_date: Start date (optional, YYYY-MM-DD)
            - end_date: End date (optional, YYYY-MM-DD)

        Returns:
            JSON response with created goal data
        """
        try:
            goal_type = request.POST.get('goal_type')
            target_hours = float(request.POST.get('target_hours', 0))
            project_id = request.POST.get('project_id')
            task_id = request.POST.get('task_id')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')

            # Validate required fields
            if not goal_type:
                return JsonResponse({
                    'error': 'Goal type is required.',
                }, status=400)

            if target_hours <= 0:
                return JsonResponse({
                    'error': 'Target duration must be positive.',
                }, status=400)

            if not project_id and not task_id:
                return JsonResponse({
                    'error': 'Either project or task is required.',
                }, status=400)

            if project_id and task_id:
                return JsonResponse({
                    'error': 'Cannot specify both project and task.',
                }, status=400)

            # Convert hours to timedelta
            target_duration = timedelta(hours=target_hours)

            # Create goal
            goal = TimeGoal.objects.create(
                user=request.user,
                goal_type=goal_type,
                target_duration=target_duration,
                project_id=project_id if project_id else None,
                task_id=task_id if task_id else None,
                start_date=start_date if start_date else None,
                end_date=end_date if end_date else None,
                is_active=True,
            )

            logger.info(f"Created time goal {goal.id} for user {request.user.id}")

            return JsonResponse({
                'success': True,
                'goal': {
                    'id': goal.id,
                    'goal_type': goal.goal_type,
                    'target_duration': str(goal.target_duration),
                    'project_id': goal.project_id,
                    'task_id': goal.task_id,
                },
            }, status=201)

        except ValueError as e:
            return JsonResponse({
                'error': f'Invalid input: {str(e)}',
            }, status=400)
        except Exception as e:
            logger.error(f"Error creating time goal: {e}")
            return JsonResponse({
                'error': 'Failed to create time goal. Please try again.',
            }, status=500)


class TimeGoalUpdateAPIView(LoginRequiredMixin, View):
    """
    API endpoint to update an existing time goal.
    """

    def post(self, request, goal_id):
        """
        Update a time goal.

        URL params:
            - goal_id: ID of the time goal

        Request body:
            - target_hours: Updated target duration in hours
            - is_active: Whether goal is active (true/false)

        Returns:
            JSON response with updated goal data
        """
        try:
            goal = get_object_or_404(
                TimeGoal,
                id=goal_id,
                user=request.user
            )

            # Update fields if provided
            target_hours = request.POST.get('target_hours')
            if target_hours:
                target_hours = float(target_hours)
                if target_hours > 0:
                    goal.target_duration = timedelta(hours=target_hours)

            is_active = request.POST.get('is_active')
            if is_active is not None:
                goal.is_active = is_active.lower() == 'true'

            goal.save()

            logger.info(f"Updated time goal {goal.id} for user {request.user.id}")

            return JsonResponse({
                'success': True,
                'goal': {
                    'id': goal.id,
                    'target_duration': str(goal.target_duration),
                    'is_active': goal.is_active,
                },
            })

        except ValueError as e:
            return JsonResponse({
                'error': f'Invalid input: {str(e)}',
            }, status=400)
        except Exception as e:
            logger.error(f"Error updating time goal: {e}")
            return JsonResponse({
                'error': 'Failed to update time goal. Please try again.',
            }, status=500)


class TimeGoalDeleteAPIView(LoginRequiredMixin, View):
    """
    API endpoint to delete a time goal.
    """

    def post(self, request, goal_id):
        """
        Delete a time goal (or mark as inactive).

        URL params:
            - goal_id: ID of the time goal

        Returns:
            JSON response confirming deletion
        """
        try:
            goal = get_object_or_404(
                TimeGoal,
                id=goal_id,
                user=request.user
            )

            # Soft delete by marking as inactive
            goal.is_active = False
            goal.save()

            logger.info(f"Deleted time goal {goal.id} for user {request.user.id}")

            return JsonResponse({
                'success': True,
                'message': 'Time goal deleted successfully.',
            })

        except Exception as e:
            logger.error(f"Error deleting time goal: {e}")
            return JsonResponse({
                'error': 'Failed to delete time goal. Please try again.',
            }, status=500)
