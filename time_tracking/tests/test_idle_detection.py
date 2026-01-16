"""
Tests for idle time detection functionality.

Focused on critical behaviors:
- Idle threshold detection
- Notification sent when threshold exceeded
- User actions (keep/discard/stop) apply correctly
"""
import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from time_tracking.models import (
    TimeEntry,
    UserTimePreferences,
    IdleTimeNotification,
)
from time_tracking.tasks import check_idle_timers
from tasks.models import TaskList, Task


@pytest.mark.django_db
class TestIdleDetection:
    """Test idle timer detection logic."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def task_list(self, user):
        """Create test task list."""
        return TaskList.objects.create(
            name='Test Project',
            owner=user
        )

    @pytest.fixture
    def task(self, task_list):
        """Create test task."""
        return Task.objects.create(
            title='Test Task',
            task_list=task_list
        )

    @pytest.fixture
    def preferences(self, user):
        """Create user time preferences with 5-minute idle threshold."""
        return UserTimePreferences.objects.create(
            user=user,
            idle_threshold_minutes=5
        )

    def test_idle_notification_created_when_threshold_exceeded(self, user, task, preferences):
        """Test that idle notification is created when timer exceeds idle threshold."""
        # Create active timer that started 10 minutes ago (exceeds 5-minute threshold)
        start_time = timezone.now() - timedelta(minutes=10)
        time_entry = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task.task_list,
            start_time=start_time,
            duration=timedelta(0),
            is_running=True
        )

        # Run idle detection task
        result = check_idle_timers()

        # Verify notification was created
        assert result['status'] == 'success'
        assert result['notifications_created'] == 1

        # Verify notification details
        notification = IdleTimeNotification.objects.get(time_entry=time_entry)
        assert notification.user == user
        assert notification.action_taken == 'none'

        # Idle start should be timer start + threshold
        expected_idle_start = start_time + timedelta(minutes=5)
        assert notification.idle_start_time == expected_idle_start

    def test_no_notification_when_under_threshold(self, user, task, preferences):
        """Test that no notification is created when timer is under idle threshold."""
        # Create active timer that started 3 minutes ago (under 5-minute threshold)
        start_time = timezone.now() - timedelta(minutes=3)
        time_entry = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task.task_list,
            start_time=start_time,
            duration=timedelta(0),
            is_running=True
        )

        # Run idle detection task
        result = check_idle_timers()

        # Verify no notification was created
        assert result['status'] == 'success'
        assert result['notifications_created'] == 0
        assert IdleTimeNotification.objects.count() == 0

    def test_no_duplicate_notifications(self, user, task, preferences):
        """Test that duplicate notifications are not created for same timer."""
        # Create active timer that started 10 minutes ago
        start_time = timezone.now() - timedelta(minutes=10)
        time_entry = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task.task_list,
            start_time=start_time,
            duration=timedelta(0),
            is_running=True
        )

        # Run idle detection task twice
        result1 = check_idle_timers()
        result2 = check_idle_timers()

        # First run should create notification
        assert result1['notifications_created'] == 1

        # Second run should not create duplicate
        assert result2['notifications_created'] == 0
        assert result2['already_notified'] == 1

        # Verify only one notification exists
        assert IdleTimeNotification.objects.filter(time_entry=time_entry).count() == 1

    def test_keep_action_marks_notification(self, user, task, preferences):
        """Test that keep action marks notification without changing timer."""
        # Create timer and notification
        start_time = timezone.now() - timedelta(minutes=10)
        time_entry = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task.task_list,
            start_time=start_time,
            duration=timedelta(0),
            is_running=True
        )

        idle_start_time = start_time + timedelta(minutes=5)
        notification = IdleTimeNotification.objects.create(
            user=user,
            time_entry=time_entry,
            idle_start_time=idle_start_time
        )

        # Perform keep action
        notification.mark_action('keep')
        notification.refresh_from_db()

        # Verify notification marked
        assert notification.action_taken == 'keep'
        assert notification.action_taken_at is not None

        # Verify timer unchanged
        time_entry.refresh_from_db()
        assert time_entry.is_running is True
        assert time_entry.end_time is None

    def test_discard_action_removes_idle_time(self, user, task, preferences):
        """Test that discard action removes idle time from timer."""
        # Create timer and notification
        start_time = timezone.now() - timedelta(minutes=10)
        time_entry = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task.task_list,
            start_time=start_time,
            duration=timedelta(0),
            is_running=True
        )

        idle_start_time = start_time + timedelta(minutes=5)
        notification = IdleTimeNotification.objects.create(
            user=user,
            time_entry=time_entry,
            idle_start_time=idle_start_time
        )

        # Simulate discard action (what idle_views would do)
        time_entry.end_time = idle_start_time
        time_entry.is_running = False
        time_entry.duration = idle_start_time - start_time
        time_entry.save()

        notification.mark_action('discard')

        # Verify notification marked
        notification.refresh_from_db()
        assert notification.action_taken == 'discard'

        # Verify timer stopped at idle start with correct duration
        time_entry.refresh_from_db()
        assert time_entry.is_running is False
        assert time_entry.end_time == idle_start_time
        assert time_entry.duration == timedelta(minutes=5)

    def test_stop_action_stops_timer_at_idle_start(self, user, task, preferences):
        """Test that stop action stops timer at idle start time."""
        # Create timer and notification
        start_time = timezone.now() - timedelta(minutes=10)
        time_entry = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task.task_list,
            start_time=start_time,
            duration=timedelta(0),
            is_running=True
        )

        idle_start_time = start_time + timedelta(minutes=5)
        notification = IdleTimeNotification.objects.create(
            user=user,
            time_entry=time_entry,
            idle_start_time=idle_start_time
        )

        # Simulate stop action (what idle_views would do)
        time_entry.end_time = idle_start_time
        time_entry.is_running = False
        time_entry.duration = idle_start_time - start_time
        time_entry.save()

        notification.mark_action('stop_at_idle')

        # Verify notification marked
        notification.refresh_from_db()
        assert notification.action_taken == 'stop_at_idle'

        # Verify timer stopped at idle start
        time_entry.refresh_from_db()
        assert time_entry.is_running is False
        assert time_entry.end_time == idle_start_time
        assert time_entry.duration == timedelta(minutes=5)

    def test_idle_detection_disabled_when_threshold_zero(self, user, task):
        """Test that idle detection is skipped when threshold is 0."""
        # Create preferences with threshold disabled
        UserTimePreferences.objects.create(
            user=user,
            idle_threshold_minutes=0
        )

        # Create active timer
        start_time = timezone.now() - timedelta(minutes=10)
        time_entry = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task.task_list,
            start_time=start_time,
            duration=timedelta(0),
            is_running=True
        )

        # Run idle detection task
        result = check_idle_timers()

        # Verify no notification created
        assert result['status'] == 'success'
        assert result['notifications_created'] == 0
        assert IdleTimeNotification.objects.count() == 0

    def test_default_threshold_used_when_no_preferences(self, user, task):
        """Test that default 5-minute threshold is used when no preferences exist."""
        # Create active timer that started 10 minutes ago (exceeds default 5-minute threshold)
        start_time = timezone.now() - timedelta(minutes=10)
        time_entry = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task.task_list,
            start_time=start_time,
            duration=timedelta(0),
            is_running=True
        )

        # Run idle detection task (no preferences exist, should use default)
        result = check_idle_timers()

        # Verify notification was created with default threshold
        assert result['status'] == 'success'
        assert result['notifications_created'] == 1

        notification = IdleTimeNotification.objects.get(time_entry=time_entry)
        expected_idle_start = start_time + timedelta(minutes=5)  # Default threshold
        assert notification.idle_start_time == expected_idle_start
