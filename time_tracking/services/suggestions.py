"""
Time suggestion service for providing automatic duration suggestions based on historical data.

Analyzes past time entries to suggest durations for similar tasks.
"""
import logging
from datetime import timedelta, datetime
from typing import Optional, Dict, Any
from django.core.cache import cache
from django.db.models import Avg, Count
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class TimeSuggestion:
    """
    Service class for generating time duration suggestions based on historical patterns.

    Analyzes user's past time entries for the same or similar tasks to suggest
    realistic durations for new entries.
    """

    CACHE_KEY_PREFIX = "time_suggestion"
    CACHE_TTL = 3600  # 1 hour in seconds
    MIN_HISTORICAL_ENTRIES = 3  # Minimum entries required for suggestion

    @classmethod
    def _get_cache_key(cls, user_id: int, task_id: int, context: str = '') -> str:
        """
        Generate cache key for time suggestion.

        Args:
            user_id: User ID
            task_id: Task ID
            context: Optional context string (e.g., time of day)

        Returns:
            str: Cache key
        """
        return f"{cls.CACHE_KEY_PREFIX}:{user_id}:{task_id}:{context}"

    @classmethod
    def get_suggestion(
        cls,
        user: User,
        task,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get duration suggestion for a task based on historical data.

        Args:
            user: User requesting suggestion
            task: Task instance to get suggestion for
            context: Optional context dict with 'time_of_day', 'date', etc.

        Returns:
            dict or None: Suggestion data with 'duration', 'count', 'method' or None if insufficient data
        """
        if not user or not task:
            return None

        context = context or {}
        time_of_day = context.get('time_of_day', '')

        # Try cache first
        cache_key = cls._get_cache_key(user.id, task.id, time_of_day)
        try:
            cached_suggestion = cache.get(cache_key)
            if cached_suggestion:
                logger.debug(f"Cache hit for suggestion: user={user.id}, task={task.id}")
                return cached_suggestion
        except Exception as e:
            logger.warning(f"Cache error when fetching suggestion: {e}")

        # Calculate suggestion from database
        suggestion = cls._calculate_suggestion(user, task, context)

        # Cache the result if we have a suggestion
        if suggestion:
            try:
                cache.set(cache_key, suggestion, timeout=cls.CACHE_TTL)
            except Exception as e:
                logger.warning(f"Failed to cache suggestion: {e}")

        return suggestion

    @classmethod
    def _calculate_suggestion(
        cls,
        user: User,
        task,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate duration suggestion from historical time entries.

        Args:
            user: User instance
            task: Task instance
            context: Context dict with optional time_of_day, date, etc.

        Returns:
            dict or None: Suggestion data or None if insufficient data
        """
        from time_tracking.models import TimeEntry

        # Query historical entries for this exact task
        entries = TimeEntry.objects.filter(
            user=user,
            task=task,
            is_running=False,
            duration__isnull=False
        ).order_by('-start_time')[:20]  # Last 20 entries

        # If not enough entries for this specific task, try similar tasks
        if entries.count() < cls.MIN_HISTORICAL_ENTRIES:
            entries = cls._get_similar_task_entries(user, task)

        # Still not enough data
        if entries.count() < cls.MIN_HISTORICAL_ENTRIES:
            logger.debug(
                f"Insufficient historical data for suggestion: "
                f"user={user.id}, task={task.id}, count={entries.count()}"
            )
            return None

        # Filter by time of day if provided
        time_of_day = context.get('time_of_day')
        if time_of_day:
            entries = cls._filter_by_time_of_day(entries, time_of_day)
            # If filtering removed too many entries, use all entries
            if entries.count() < cls.MIN_HISTORICAL_ENTRIES:
                entries = TimeEntry.objects.filter(
                    user=user,
                    task=task,
                    is_running=False,
                    duration__isnull=False
                ).order_by('-start_time')[:20]

        # Calculate median duration (more robust than mean for outliers)
        durations = [entry.duration for entry in entries]
        durations.sort()

        median_duration = cls._calculate_median(durations)

        return {
            'duration': median_duration,
            'count': len(durations),
            'method': 'median',
            'task_id': task.id,
            'task_title': task.title,
        }

    @classmethod
    def _get_similar_task_entries(cls, user: User, task):
        """
        Get time entries for similar tasks based on name, project, or tags.

        Args:
            user: User instance
            task: Task instance

        Returns:
            QuerySet: Time entries for similar tasks
        """
        from time_tracking.models import TimeEntry

        # Try tasks in same project
        similar_entries = TimeEntry.objects.filter(
            user=user,
            project=task.task_list,
            is_running=False,
            duration__isnull=False
        ).exclude(task=task).order_by('-start_time')[:20]

        return similar_entries

    @classmethod
    def _filter_by_time_of_day(cls, entries, time_of_day: str):
        """
        Filter entries by time of day pattern.

        Args:
            entries: QuerySet of time entries
            time_of_day: Time period ('morning', 'afternoon', 'evening')

        Returns:
            QuerySet: Filtered entries
        """
        # Define time ranges
        time_ranges = {
            'morning': (0, 12),    # 12 AM - 12 PM
            'afternoon': (12, 17),  # 12 PM - 5 PM
            'evening': (17, 24),    # 5 PM - 12 AM
        }

        if time_of_day not in time_ranges:
            return entries

        start_hour, end_hour = time_ranges[time_of_day]

        # Filter entries that started in this time range
        filtered = [
            entry for entry in entries
            if entry.start_time and start_hour <= entry.start_time.hour < end_hour
        ]

        # Return as list (already evaluated queryset)
        return type('obj', (object,), {
            'count': lambda: len(filtered),
            '__iter__': lambda: iter(filtered)
        })()

    @classmethod
    def _calculate_median(cls, durations: list) -> timedelta:
        """
        Calculate median duration from list of timedeltas.

        Args:
            durations: List of timedelta objects

        Returns:
            timedelta: Median duration
        """
        if not durations:
            return timedelta(0)

        n = len(durations)
        if n % 2 == 0:
            # Even number: average of two middle values
            mid1 = durations[n // 2 - 1]
            mid2 = durations[n // 2]
            median_seconds = (mid1.total_seconds() + mid2.total_seconds()) / 2
            return timedelta(seconds=median_seconds)
        else:
            # Odd number: middle value
            return durations[n // 2]

    @classmethod
    def format_suggestion(cls, suggestion: Dict[str, Any]) -> str:
        """
        Format suggestion for display in UI.

        Args:
            suggestion: Suggestion dict from get_suggestion()

        Returns:
            str: Formatted suggestion text
        """
        if not suggestion:
            return ''

        duration = suggestion['duration']
        count = suggestion['count']

        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)

        if hours > 0:
            duration_str = f"{hours}h {minutes}m"
        else:
            duration_str = f"{minutes}m"

        entry_word = "entry" if count == 1 else "entries"
        return f"Suggested: {duration_str} (based on {count} previous {entry_word})"

    @classmethod
    def clear_cache_for_task(cls, user_id: int, task_id: int):
        """
        Clear cached suggestions for a specific task.

        Called when new time entries are created to ensure fresh suggestions.

        Args:
            user_id: User ID
            task_id: Task ID
        """
        for time_context in ['', 'morning', 'afternoon', 'evening']:
            cache_key = cls._get_cache_key(user_id, task_id, time_context)
            try:
                cache.delete(cache_key)
            except Exception as e:
                logger.warning(f"Failed to clear suggestion cache: {e}")
