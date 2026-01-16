"""
Redis cache service for active timer state management.

Provides fast access to active timer data with automatic fallback to PostgreSQL
when Redis is unavailable.
"""
import json
import logging
from typing import Optional, Dict, Any
from django.core.cache import cache
from django.core.cache.backends.base import InvalidCacheBackendError
from django.utils import timezone

logger = logging.getLogger(__name__)


class TimeEntryCache:
    """
    Service class for managing active timer state in Redis cache.

    Implements automatic fallback to PostgreSQL when Redis is unavailable,
    ensuring timer functionality continues even during cache failures.
    """

    CACHE_KEY_PREFIX = "timer:active"
    CACHE_TTL = 86400  # 24 hours in seconds

    @classmethod
    def _get_cache_key(cls, user_id: int) -> str:
        """
        Generate Redis cache key for user's active timer.

        Args:
            user_id: User ID

        Returns:
            str: Cache key in format "timer:active:{user_id}"
        """
        return f"{cls.CACHE_KEY_PREFIX}:{user_id}"

    @classmethod
    def _serialize_timer_data(cls, time_entry) -> Dict[str, Any]:
        """
        Serialize TimeEntry instance to cache-safe dictionary.

        Args:
            time_entry: TimeEntry instance

        Returns:
            dict: Serialized timer data
        """
        return {
            'id': time_entry.id,
            'user_id': time_entry.user_id,
            'task_id': time_entry.task_id,
            'task_title': time_entry.task.title if time_entry.task else None,
            'project_id': time_entry.project_id,
            'project_name': time_entry.project.name if time_entry.project else None,
            'start_time': time_entry.start_time.isoformat() if time_entry.start_time else None,
            'description': time_entry.description,
            'is_running': time_entry.is_running,
            'created_at': time_entry.created_at.isoformat(),
        }

    @classmethod
    def set_active_timer(cls, user_id: int, time_entry) -> bool:
        """
        Store active timer data in Redis cache.

        Args:
            user_id: User ID
            time_entry: TimeEntry instance to cache

        Returns:
            bool: True if cached successfully, False if cache unavailable
        """
        try:
            cache_key = cls._get_cache_key(user_id)
            timer_data = cls._serialize_timer_data(time_entry)
            cache.set(cache_key, json.dumps(timer_data), timeout=cls.CACHE_TTL)
            logger.debug(f"Cached active timer for user {user_id}")
            return True
        except (InvalidCacheBackendError, ConnectionError, Exception) as e:
            logger.warning(f"Failed to cache timer for user {user_id}: {e}")
            return False

    @classmethod
    def get_active_timer(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve active timer data from Redis cache.

        Falls back to PostgreSQL query if cache miss or Redis unavailable.

        Args:
            user_id: User ID

        Returns:
            dict or None: Timer data if active timer exists, None otherwise
        """
        try:
            cache_key = cls._get_cache_key(user_id)
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.debug(f"Cache hit for user {user_id} active timer")
                return json.loads(cached_data)

            logger.debug(f"Cache miss for user {user_id}, falling back to PostgreSQL")

        except (InvalidCacheBackendError, ConnectionError, Exception) as e:
            logger.warning(f"Cache error for user {user_id}, falling back to PostgreSQL: {e}")

        # Fallback to PostgreSQL
        return cls._get_from_database(user_id)

    @classmethod
    def _get_from_database(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Fallback method to retrieve active timer from PostgreSQL.

        Args:
            user_id: User ID

        Returns:
            dict or None: Timer data if active timer exists, None otherwise
        """
        from time_tracking.models import TimeEntry

        try:
            time_entry = TimeEntry.objects.select_related('task', 'project').filter(
                user_id=user_id,
                is_running=True
            ).first()

            if time_entry:
                timer_data = cls._serialize_timer_data(time_entry)
                # Try to repopulate cache
                cls.set_active_timer(user_id, time_entry)
                return timer_data

            return None

        except Exception as e:
            logger.error(f"Database query error for user {user_id}: {e}")
            return None

    @classmethod
    def clear_active_timer(cls, user_id: int) -> bool:
        """
        Clear active timer from Redis cache.

        Args:
            user_id: User ID

        Returns:
            bool: True if cleared successfully, False if cache unavailable
        """
        try:
            cache_key = cls._get_cache_key(user_id)
            cache.delete(cache_key)
            logger.debug(f"Cleared active timer cache for user {user_id}")
            return True
        except (InvalidCacheBackendError, ConnectionError, Exception) as e:
            logger.warning(f"Failed to clear timer cache for user {user_id}: {e}")
            return False

    @classmethod
    def sync_to_db(cls, user_id: int) -> bool:
        """
        Synchronize cached timer state to PostgreSQL database.

        Ensures cache and database remain consistent by updating database
        with current timer state from cache.

        Args:
            user_id: User ID

        Returns:
            bool: True if synchronized successfully, False otherwise
        """
        from time_tracking.models import TimeEntry

        try:
            # Get cached timer data
            timer_data = cls.get_active_timer(user_id)

            if not timer_data:
                logger.debug(f"No active timer to sync for user {user_id}")
                return True

            # Update database record
            time_entry = TimeEntry.objects.filter(
                id=timer_data['id'],
                user_id=user_id,
                is_running=True
            ).first()

            if time_entry:
                # Update fields that might have changed
                time_entry.description = timer_data.get('description', '')
                time_entry.save(update_fields=['description', 'updated_at'])
                logger.debug(f"Synced timer {time_entry.id} to database for user {user_id}")
                return True
            else:
                # Timer was stopped/deleted, clear cache
                cls.clear_active_timer(user_id)
                logger.debug(f"Timer not found in DB, cleared cache for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to sync timer to DB for user {user_id}: {e}")
            return False

    @classmethod
    def restore_from_db(cls) -> int:
        """
        Restore all active timers from PostgreSQL to Redis cache.

        Called on application startup to repopulate cache with active timers.

        Returns:
            int: Number of timers restored to cache
        """
        from time_tracking.models import TimeEntry

        restored_count = 0

        try:
            active_timers = TimeEntry.objects.select_related('task', 'project').filter(
                is_running=True
            )

            for time_entry in active_timers:
                if cls.set_active_timer(time_entry.user_id, time_entry):
                    restored_count += 1

            logger.info(f"Restored {restored_count} active timers to cache from PostgreSQL")
            return restored_count

        except Exception as e:
            logger.error(f"Failed to restore timers from database: {e}")
            return restored_count
