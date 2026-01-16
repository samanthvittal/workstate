"""
Serializers for time tracking API responses.

Provides JSON serialization for TimeEntry and related models.
"""
from datetime import timedelta
from django.utils import timezone


class TimeEntrySerializer:
    """
    Serializer for TimeEntry instances to JSON-safe dictionaries.

    Converts TimeEntry model instances to dictionaries suitable for JSON
    responses, calculating elapsed time for running timers.
    """

    @staticmethod
    def serialize(time_entry):
        """
        Serialize TimeEntry instance to dictionary.

        Args:
            time_entry: TimeEntry instance

        Returns:
            dict: Serialized timer data
        """
        data = {
            'id': time_entry.id,
            'user_id': time_entry.user_id,
            'task': {
                'id': time_entry.task_id,
                'title': time_entry.task.title if time_entry.task else None,
            },
            'project': None,
            'start_time': time_entry.start_time.isoformat() if time_entry.start_time else None,
            'end_time': time_entry.end_time.isoformat() if time_entry.end_time else None,
            'duration': int(time_entry.duration.total_seconds()) if time_entry.duration else 0,
            'description': time_entry.description,
            'is_running': time_entry.is_running,
            'is_billable': time_entry.is_billable,
            'billable_rate': str(time_entry.billable_rate) if time_entry.billable_rate else None,
            'currency': time_entry.currency,
            'created_at': time_entry.created_at.isoformat(),
            'updated_at': time_entry.updated_at.isoformat(),
        }

        # Add project info if available
        if time_entry.project:
            data['project'] = {
                'id': time_entry.project_id,
                'name': time_entry.project.name,
            }

        # Add elapsed time for running timers
        if time_entry.is_running:
            elapsed = time_entry.get_elapsed_time()
            data['elapsed_time'] = int(elapsed.total_seconds()) if elapsed else 0
        else:
            data['elapsed_time'] = int(time_entry.duration.total_seconds()) if time_entry.duration else 0

        return data

    @staticmethod
    def serialize_confirmation_dialog(current_timer, new_task):
        """
        Serialize confirmation dialog data for auto-stop scenario.

        Args:
            current_timer: Currently running TimeEntry instance
            new_task: Task instance for new timer

        Returns:
            dict: Confirmation dialog data
        """
        elapsed = current_timer.get_elapsed_time()

        return {
            'confirmation_required': True,
            'current_timer': {
                'id': current_timer.id,
                'task': {
                    'id': current_timer.task_id,
                    'title': current_timer.task.title if current_timer.task else None,
                },
                'project': {
                    'id': current_timer.project_id,
                    'name': current_timer.project.name if current_timer.project else None,
                },
                'start_time': current_timer.start_time.isoformat() if current_timer.start_time else None,
                'elapsed_time': int(elapsed.total_seconds()) if elapsed else 0,
                'description': current_timer.description,
            },
            'new_task': {
                'id': new_task.id,
                'title': new_task.title,
                'project': {
                    'id': new_task.task_list_id,
                    'name': new_task.task_list.name if new_task.task_list else None,
                },
            },
            'message': 'You have an active timer running. What would you like to do?',
        }

    @staticmethod
    def serialize_discard_confirmation(active_timer):
        """
        Serialize confirmation data for timer discard.

        Args:
            active_timer: Active TimeEntry instance

        Returns:
            dict: Discard confirmation data
        """
        elapsed = active_timer.get_elapsed_time()

        return {
            'confirmation_required': True,
            'timer': {
                'id': active_timer.id,
                'task': {
                    'id': active_timer.task_id,
                    'title': active_timer.task.title if active_timer.task else None,
                },
                'elapsed_time': int(elapsed.total_seconds()) if elapsed else 0,
                'description': active_timer.description,
            },
            'message': 'Are you sure you want to discard this timer? This action cannot be undone.',
        }
