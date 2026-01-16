"""
Time Entry CRUD API views for manual time entry management.

Provides JSON API endpoints for creating, reading, updating, and deleting
time entries with support for three input modes and comprehensive validation.
"""
import json
import logging
from datetime import timedelta, datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views import View

from tasks.models import Task
from time_tracking.models import TimeEntry, UserTimePreferences
from time_tracking.serializers import TimeEntrySerializer

logger = logging.getLogger(__name__)


class TimeEntryAPIView(LoginRequiredMixin, View):
    """
    Base view for time entry CRUD API endpoints.

    Provides common functionality for authentication, JSON parsing,
    and error handling.
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


class TimeEntryListView(TimeEntryAPIView):
    """
    List time entries endpoint.

    GET /api/time-entries/
    Query params: project_id, task_id, start_date, end_date, is_billable

    Returns paginated list of time entries with related data.
    """

    def get(self, request):
        """Handle list time entries request."""
        try:
            # Build queryset with permission check
            queryset = TimeEntry.objects.filter(
                user=request.user,
                is_running=False  # Exclude running timers from list
            ).select_related(
                'task',
                'project',
                'user'
            ).prefetch_related(
                'time_entry_tags__tag'
            ).order_by('-start_time', '-created_at')

            # Apply filters (basic implementation, enhanced in Task Group 7)
            project_id = request.GET.get('project_id')
            if project_id:
                queryset = queryset.filter(project_id=project_id)

            task_id = request.GET.get('task_id')
            if task_id:
                queryset = queryset.filter(task_id=task_id)

            # Simple pagination (default 50 per page)
            page_size = 50
            entries = queryset[:page_size]

            # Serialize entries
            data = {
                'results': [self._serialize_entry(entry) for entry in entries],
                'count': len(entries),
            }

            return self.success_response(data, status=200)

        except Exception as e:
            logger.error(f"Unexpected error listing time entries: {e}", exc_info=True)
            return self.error_response(
                'An error occurred while retrieving time entries. Please try again.',
                status=500
            )

    def _serialize_entry(self, entry):
        """
        Serialize time entry with related data.

        Args:
            entry: TimeEntry instance

        Returns:
            dict: Serialized entry data
        """
        data = TimeEntrySerializer.serialize(entry)

        # Add tags
        tags = [
            {'id': tag_rel.tag_id, 'name': tag_rel.tag.name}
            for tag_rel in entry.time_entry_tags.all()
        ]
        data['tags'] = tags

        return data


class TimeEntryRetrieveView(TimeEntryAPIView):
    """
    Retrieve single time entry endpoint.

    GET /api/time-entries/{id}/

    Returns single time entry with all related data.
    """

    def get(self, request, entry_id):
        """Handle retrieve time entry request."""
        try:
            # Get entry with permission check
            try:
                entry = TimeEntry.objects.select_related(
                    'task',
                    'project',
                    'user'
                ).prefetch_related(
                    'time_entry_tags__tag'
                ).get(
                    id=entry_id,
                    user=request.user
                )
            except TimeEntry.DoesNotExist:
                return self.error_response(
                    'Time entry not found.',
                    status=404
                )

            # Serialize and return
            data = TimeEntrySerializer.serialize(entry)

            # Add tags
            tags = [
                {'id': tag_rel.tag_id, 'name': tag_rel.tag.name}
                for tag_rel in entry.time_entry_tags.all()
            ]
            data['tags'] = tags

            return self.success_response(data, status=200)

        except Exception as e:
            logger.error(f"Unexpected error retrieving time entry: {e}", exc_info=True)
            return self.error_response(
                'An error occurred while retrieving the time entry. Please try again.',
                status=500
            )


class TimeEntryCreateView(TimeEntryAPIView):
    """
    Create time entry endpoint.

    POST /api/time-entries/
    Body: {task_id, start_time?, end_time?, duration?, description?, is_billable?, billable_rate?}

    Supports three input modes:
    - Mode A: start_time + end_time (calculate duration)
    - Mode B: start_time + duration (calculate end_time)
    - Mode C: duration only (no timestamps)
    """

    def post(self, request):
        """Handle create time entry request."""
        try:
            # Parse request data
            data = self.parse_json_body(request)
            task_id = data.get('task_id')
            start_time_str = data.get('start_time')
            end_time_str = data.get('end_time')
            duration_seconds = data.get('duration')
            description = data.get('description', '').strip()
            is_billable = data.get('is_billable', False)
            billable_rate = data.get('billable_rate')
            currency = data.get('currency', 'USD')

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

            # Parse timestamps if provided
            start_time = None
            end_time = None

            if start_time_str:
                start_time = self._parse_datetime(start_time_str)
                if not start_time:
                    return self.error_response(
                        'Invalid start_time format.',
                        field='start_time'
                    )

            if end_time_str:
                end_time = self._parse_datetime(end_time_str)
                if not end_time:
                    return self.error_response(
                        'Invalid end_time format.',
                        field='end_time'
                    )

            # Determine mode and calculate missing fields
            duration = None

            # Mode A: start_time + end_time provided
            if start_time and end_time:
                if end_time <= start_time:
                    return self.error_response(
                        'End time must be after start time.',
                        field='end_time'
                    )
                duration = end_time - start_time

            # Mode B: start_time + duration provided
            elif start_time and duration_seconds is not None:
                duration = timedelta(seconds=duration_seconds)
                if duration <= timedelta(0):
                    return self.error_response(
                        'Duration must be positive.',
                        field='duration'
                    )
                end_time = start_time + duration

            # Mode C: duration only
            elif duration_seconds is not None:
                duration = timedelta(seconds=duration_seconds)
                if duration <= timedelta(0):
                    return self.error_response(
                        'Duration must be positive.',
                        field='duration'
                    )
                # start_time and end_time remain None

            # Validate: cannot have end_time without start_time
            elif end_time and not start_time:
                return self.error_response(
                    'Cannot specify end_time without start_time.',
                    field='end_time'
                )

            else:
                return self.error_response(
                    'Must provide either start_time + end_time, start_time + duration, or duration only.',
                    field='duration'
                )

            # Apply time rounding rules from UserTimePreferences
            try:
                preferences = request.user.time_preferences
                if preferences.rounding_interval > 0 and duration:
                    # Create temporary entry for rounding calculation
                    temp_entry = TimeEntry(duration=duration)
                    rounded_duration = temp_entry.apply_rounding(
                        preferences.rounding_interval,
                        preferences.rounding_method
                    )
                    if rounded_duration > timedelta(0):
                        duration = rounded_duration
                        # Recalculate end_time if mode B
                        if start_time and not end_time_str:
                            end_time = start_time + duration
            except UserTimePreferences.DoesNotExist:
                # No preferences set, use actual duration (no rounding)
                pass

            # Create time entry with transaction
            with transaction.atomic():
                time_entry = TimeEntry(
                    user=request.user,
                    task=task,
                    project=task.task_list,  # Inherit project from task
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    description=description,
                    is_running=False,
                    is_billable=is_billable,
                    billable_rate=billable_rate if billable_rate else None,
                    currency=currency,
                )
                time_entry.save()

                logger.info(f"Created time entry {time_entry.id} for user {request.user.id}")

                # Return created time entry data
                entry_data = TimeEntrySerializer.serialize(time_entry)
                return self.success_response(entry_data, status=201)

        except ValueError as e:
            return self.error_response(str(e), status=400)
        except ValidationError as e:
            # Extract first error message
            if hasattr(e, 'message_dict'):
                first_field = list(e.message_dict.keys())[0]
                first_error = e.message_dict[first_field][0]
                return self.error_response(first_error, field=first_field)
            return self.error_response(str(e), status=400)
        except Exception as e:
            logger.error(f"Unexpected error creating time entry: {e}", exc_info=True)
            return self.error_response(
                'An error occurred while creating the time entry. Please try again.',
                status=500
            )

    def _parse_datetime(self, datetime_str):
        """
        Parse ISO format datetime string.

        Args:
            datetime_str: ISO format datetime string

        Returns:
            datetime: Parsed datetime, or None if invalid
        """
        try:
            # Handle timezone-aware datetime strings
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str.replace('Z', '+00:00')
            return datetime.fromisoformat(datetime_str)
        except (ValueError, AttributeError):
            return None


class TimeEntryUpdateView(TimeEntryAPIView):
    """
    Update time entry endpoint.

    PATCH /api/time-entries/{id}/
    Body: {start_time?, end_time?, duration?, description?, is_billable?, billable_rate?}

    Allows editing all fields except user_id.
    Prevents editing running timers.
    """

    def patch(self, request, entry_id):
        """Handle update time entry request."""
        try:
            # Get entry with permission check
            try:
                entry = TimeEntry.objects.select_related('task').get(
                    id=entry_id,
                    user=request.user
                )
            except TimeEntry.DoesNotExist:
                return self.error_response(
                    'Time entry not found.',
                    status=404
                )

            # Prevent editing running timers
            if entry.is_running:
                return self.error_response(
                    'Cannot edit running timer. Use timer API to stop timer first.',
                    status=400
                )

            # Parse request data
            data = self.parse_json_body(request)

            # Update fields with transaction
            with transaction.atomic():
                # Update timestamp fields if provided
                if 'start_time' in data:
                    start_time_str = data['start_time']
                    if start_time_str:
                        entry.start_time = self._parse_datetime(start_time_str)
                        if not entry.start_time:
                            return self.error_response(
                                'Invalid start_time format.',
                                field='start_time'
                            )
                    else:
                        entry.start_time = None

                if 'end_time' in data:
                    end_time_str = data['end_time']
                    if end_time_str:
                        entry.end_time = self._parse_datetime(end_time_str)
                        if not entry.end_time:
                            return self.error_response(
                                'Invalid end_time format.',
                                field='end_time'
                            )
                    else:
                        entry.end_time = None

                # Recalculate duration if start_time or end_time changed
                if 'start_time' in data or 'end_time' in data:
                    if entry.start_time and entry.end_time:
                        if entry.end_time <= entry.start_time:
                            return self.error_response(
                                'End time must be after start time.',
                                field='end_time'
                            )
                        entry.duration = entry.end_time - entry.start_time

                # Update duration if provided
                if 'duration' in data:
                    duration_seconds = data['duration']
                    if duration_seconds is not None:
                        entry.duration = timedelta(seconds=duration_seconds)
                        if entry.duration <= timedelta(0):
                            return self.error_response(
                                'Duration must be positive.',
                                field='duration'
                            )

                        # Recalculate end_time if start_time set
                        if entry.start_time and 'end_time' not in data:
                            entry.end_time = entry.start_time + entry.duration

                # Update other fields
                if 'description' in data:
                    entry.description = data['description'].strip()

                if 'is_billable' in data:
                    entry.is_billable = data['is_billable']

                if 'billable_rate' in data:
                    entry.billable_rate = data['billable_rate'] if data['billable_rate'] else None

                if 'currency' in data:
                    entry.currency = data['currency']

                # Apply time rounding rules to updated duration
                try:
                    preferences = request.user.time_preferences
                    if preferences.rounding_interval > 0 and entry.duration:
                        rounded_duration = entry.apply_rounding(
                            preferences.rounding_interval,
                            preferences.rounding_method
                        )
                        if rounded_duration > timedelta(0):
                            entry.duration = rounded_duration
                            # Recalculate end_time if start_time set
                            if entry.start_time and 'end_time' not in data:
                                entry.end_time = entry.start_time + entry.duration
                except UserTimePreferences.DoesNotExist:
                    pass

                # Save entry
                entry.save()

                logger.info(f"Updated time entry {entry.id} for user {request.user.id}")

                # Return updated time entry data
                entry_data = TimeEntrySerializer.serialize(entry)
                return self.success_response(entry_data, status=200)

        except ValueError as e:
            return self.error_response(str(e), status=400)
        except ValidationError as e:
            # Extract first error message
            if hasattr(e, 'message_dict'):
                first_field = list(e.message_dict.keys())[0]
                first_error = e.message_dict[first_field][0]
                return self.error_response(first_error, field=first_field)
            return self.error_response(str(e), status=400)
        except Exception as e:
            logger.error(f"Unexpected error updating time entry: {e}", exc_info=True)
            return self.error_response(
                'An error occurred while updating the time entry. Please try again.',
                status=500
            )

    def _parse_datetime(self, datetime_str):
        """
        Parse ISO format datetime string.

        Args:
            datetime_str: ISO format datetime string

        Returns:
            datetime: Parsed datetime, or None if invalid
        """
        try:
            # Handle timezone-aware datetime strings
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str.replace('Z', '+00:00')
            return datetime.fromisoformat(datetime_str)
        except (ValueError, AttributeError):
            return None


class TimeEntryDeleteView(TimeEntryAPIView):
    """
    Delete time entry endpoint.

    DELETE /api/time-entries/{id}/

    Deletes time entry. Prevents deleting running timers.
    """

    def delete(self, request, entry_id):
        """Handle delete time entry request."""
        try:
            # Get entry with permission check
            try:
                entry = TimeEntry.objects.get(
                    id=entry_id,
                    user=request.user
                )
            except TimeEntry.DoesNotExist:
                return self.error_response(
                    'Time entry not found.',
                    status=404
                )

            # Prevent deleting running timers
            if entry.is_running:
                return self.error_response(
                    'Cannot delete running timer. Use timer discard API instead.',
                    status=400
                )

            # Delete entry with transaction
            with transaction.atomic():
                entry_id_deleted = entry.id
                entry.delete()

                logger.info(f"Deleted time entry {entry_id_deleted} for user {request.user.id}")

                # Return 204 No Content on success
                return JsonResponse({}, status=204)

        except Exception as e:
            logger.error(f"Unexpected error deleting time entry: {e}", exc_info=True)
            return self.error_response(
                'An error occurred while deleting the time entry. Please try again.',
                status=500
            )
