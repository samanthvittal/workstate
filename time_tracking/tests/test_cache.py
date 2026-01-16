"""
Focused tests for Redis cache operations.

Tests cover only critical cache operations:
- Set active timer in cache
- Get active timer from cache
- Clear timer from cache
- Fallback to PostgreSQL on Redis failure
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from time_tracking.models import TimeEntry
from time_tracking.services.cache import TimeEntryCache
from tasks.models import Task, TaskList
from accounts.models import Workspace


@pytest.mark.django_db
class TestTimeEntryCache:
    """Test critical Redis cache operations."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test."""
        cache.clear()
        yield
        cache.clear()

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def workspace(self, user):
        """Create test workspace."""
        return Workspace.objects.create(
            name='Test Workspace',
            owner=user
        )

    @pytest.fixture
    def task_list(self, workspace, user):
        """Create test task list."""
        return TaskList.objects.create(
            name='Test Project',
            workspace=workspace,
            created_by=user
        )

    @pytest.fixture
    def task(self, task_list, user):
        """Create test task."""
        return Task.objects.create(
            title='Test Task',
            priority='P3',
            task_list=task_list,
            created_by=user
        )

    @pytest.fixture
    def active_timer(self, user, task, task_list):
        """Create active timer in database."""
        return TimeEntry.objects.create(
            user=user,
            task=task,
            project=task_list,
            start_time=timezone.now(),
            duration=timedelta(0),
            is_running=True,
            description='Test timer'
        )

    def test_set_active_timer(self, user, active_timer):
        """Test storing active timer in Redis cache."""
        # Set timer in cache
        result = TimeEntryCache.set_active_timer(user.id, active_timer)

        # Verify cache operation succeeded
        assert result is True

        # Verify data is in cache
        cache_key = TimeEntryCache._get_cache_key(user.id)
        cached_data = cache.get(cache_key)
        assert cached_data is not None

        # Verify cached data structure
        timer_data = json.loads(cached_data)
        assert timer_data['id'] == active_timer.id
        assert timer_data['user_id'] == user.id
        assert timer_data['task_id'] == active_timer.task_id
        assert timer_data['is_running'] is True

    def test_get_active_timer_from_cache(self, user, active_timer):
        """Test retrieving active timer from Redis cache."""
        # Set timer in cache first
        TimeEntryCache.set_active_timer(user.id, active_timer)

        # Get timer from cache
        timer_data = TimeEntryCache.get_active_timer(user.id)

        # Verify data retrieved correctly
        assert timer_data is not None
        assert timer_data['id'] == active_timer.id
        assert timer_data['user_id'] == user.id
        assert timer_data['task_id'] == active_timer.task_id
        assert timer_data['is_running'] is True

    def test_get_active_timer_fallback_to_database(self, user, active_timer):
        """Test fallback to PostgreSQL when cache miss."""
        # Don't set cache, so it will fall back to database
        timer_data = TimeEntryCache.get_active_timer(user.id)

        # Verify data retrieved from database
        assert timer_data is not None
        assert timer_data['id'] == active_timer.id
        assert timer_data['user_id'] == user.id
        assert timer_data['task_id'] == active_timer.task_id

    def test_clear_active_timer(self, user, active_timer):
        """Test clearing active timer from cache."""
        # Set timer in cache first
        TimeEntryCache.set_active_timer(user.id, active_timer)

        # Clear timer from cache
        result = TimeEntryCache.clear_active_timer(user.id)

        # Verify operation succeeded
        assert result is True

        # Verify cache is empty
        cache_key = TimeEntryCache._get_cache_key(user.id)
        cached_data = cache.get(cache_key)
        assert cached_data is None

    def test_cache_fallback_on_redis_failure(self, user, active_timer):
        """Test automatic fallback to PostgreSQL when Redis unavailable."""
        # Mock cache.get to raise exception (simulating Redis failure)
        with patch('django.core.cache.cache.get', side_effect=ConnectionError('Redis unavailable')):
            # Should fallback to database without error
            timer_data = TimeEntryCache.get_active_timer(user.id)

            # Verify data retrieved from database fallback
            assert timer_data is not None
            assert timer_data['id'] == active_timer.id
            assert timer_data['user_id'] == user.id

    def test_get_active_timer_returns_none_when_no_timer(self, user):
        """Test get_active_timer returns None when user has no active timer."""
        # Get timer when none exists
        timer_data = TimeEntryCache.get_active_timer(user.id)

        # Verify None returned
        assert timer_data is None

    def test_sync_to_db_updates_database(self, user, active_timer):
        """Test sync_to_db synchronizes cache description to PostgreSQL."""
        # Set timer in cache
        TimeEntryCache.set_active_timer(user.id, active_timer)

        # Update description in cache
        cache_key = TimeEntryCache._get_cache_key(user.id)
        cached_data = json.loads(cache.get(cache_key))
        cached_data['description'] = 'Updated description'
        cache.set(cache_key, json.dumps(cached_data), timeout=TimeEntryCache.CACHE_TTL)

        # Sync to database
        result = TimeEntryCache.sync_to_db(user.id)

        # Verify sync succeeded
        assert result is True

        # Verify database was updated with description from cache
        active_timer.refresh_from_db()
        assert active_timer.description == 'Updated description'

    def test_restore_from_db(self, user, active_timer):
        """Test restore_from_db populates cache from PostgreSQL."""
        # Clear cache first
        cache.clear()

        # Restore timers from database
        restored_count = TimeEntryCache.restore_from_db()

        # Verify at least one timer restored
        assert restored_count >= 1

        # Verify timer is in cache
        timer_data = TimeEntryCache.get_active_timer(user.id)
        assert timer_data is not None
        assert timer_data['id'] == active_timer.id
