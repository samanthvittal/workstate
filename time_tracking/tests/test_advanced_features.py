"""
Tests for advanced time tracking features.

Tests Pomodoro timer mode, time rounding logic, and automatic time suggestions.
"""
import pytest
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from time_tracking.models import (
    TimeEntry,
    PomodoroSession,
    UserTimePreferences,
    TimeGoal,
)
from time_tracking.services.rounding import TimeRounding
from time_tracking.services.suggestions import TimeSuggestion
from tasks.models import Task, TaskList
from accounts.models import Workspace


@pytest.mark.django_db
class TestPomodoroSessionTracking:
    """Test Pomodoro session tracking functionality."""

    def test_pomodoro_session_creation(self):
        """Test creating a Pomodoro session for an active timer."""
        # Create user and task
        user = User.objects.create_user(username='testuser', password='testpass')
        workspace = Workspace.objects.create(name='Test Workspace', owner=user)
        task_list = TaskList.objects.create(name='Test List', workspace=workspace, created_by=user)
        task = Task.objects.create(title='Test Task', task_list=task_list, created_by=user, priority='P3')

        # Create active timer
        time_entry = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task_list,
            start_time=timezone.now(),
            duration=timedelta(0),
            is_running=True,
        )

        # Create Pomodoro session
        session = PomodoroSession.objects.create(
            time_entry=time_entry,
            session_number=1,
            started_at=timezone.now(),
        )

        assert session.id is not None
        assert session.session_number == 1
        assert session.was_completed is False
        assert session.break_taken is False

    def test_pomodoro_session_completion(self):
        """Test marking a Pomodoro session as completed."""
        user = User.objects.create_user(username='testuser', password='testpass')
        workspace = Workspace.objects.create(name='Test Workspace', owner=user)
        task_list = TaskList.objects.create(name='Test List', workspace=workspace, created_by=user)
        task = Task.objects.create(title='Test Task', task_list=task_list, created_by=user, priority='P3')

        time_entry = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task_list,
            start_time=timezone.now(),
            duration=timedelta(0),
            is_running=True,
        )

        session = PomodoroSession.objects.create(
            time_entry=time_entry,
            session_number=1,
            started_at=timezone.now(),
        )

        # Complete the session
        session.complete_session()

        assert session.was_completed is True
        assert session.completed_at is not None

    def test_pomodoro_break_marking(self):
        """Test marking that a break was taken after Pomodoro."""
        user = User.objects.create_user(username='testuser', password='testpass')
        workspace = Workspace.objects.create(name='Test Workspace', owner=user)
        task_list = TaskList.objects.create(name='Test List', workspace=workspace, created_by=user)
        task = Task.objects.create(title='Test Task', task_list=task_list, created_by=user, priority='P3')

        time_entry = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task_list,
            start_time=timezone.now(),
            duration=timedelta(0),
            is_running=True,
        )

        session = PomodoroSession.objects.create(
            time_entry=time_entry,
            session_number=1,
            started_at=timezone.now(),
        )

        # Mark break taken
        session.mark_break_taken()

        assert session.break_taken is True


@pytest.mark.django_db
class TestTimeRounding:
    """Test time rounding logic."""

    def test_round_up(self):
        """Test rounding up to next interval."""
        duration = timedelta(minutes=22)  # 22 minutes
        rounded = TimeRounding.round_duration(duration, 15, 'up')

        assert rounded == timedelta(minutes=30)

    def test_round_down(self):
        """Test rounding down to previous interval."""
        duration = timedelta(minutes=22)  # 22 minutes
        rounded = TimeRounding.round_duration(duration, 15, 'down')

        assert rounded == timedelta(minutes=15)

    def test_round_nearest(self):
        """Test rounding to nearest interval."""
        # 22 minutes rounds to 15 (7 min from 15, 8 min from 30)
        duration1 = timedelta(minutes=22)
        rounded1 = TimeRounding.round_duration(duration1, 15, 'nearest')
        assert rounded1 == timedelta(minutes=15)

        # 23 minutes rounds to 30 (8 min from 15, 7 min from 30)
        duration2 = timedelta(minutes=23)
        rounded2 = TimeRounding.round_duration(duration2, 15, 'nearest')
        assert rounded2 == timedelta(minutes=30)

    def test_no_rounding_when_interval_zero(self):
        """Test that no rounding occurs when interval is 0."""
        duration = timedelta(minutes=22)
        rounded = TimeRounding.round_duration(duration, 0, 'nearest')

        assert rounded == duration

    def test_rounding_info(self):
        """Test getting both actual and rounded duration."""
        duration = timedelta(minutes=22)
        info = TimeRounding.get_rounding_info(duration, 15, 'up')

        assert info['actual'] == timedelta(minutes=22)
        assert info['rounded'] == timedelta(minutes=30)
        assert info['difference'] == timedelta(minutes=8)
        assert info['applied'] is True


@pytest.mark.django_db
class TestTimeSuggestions:
    """Test automatic time suggestions."""

    def test_suggestion_with_sufficient_history(self):
        """Test that suggestion is generated with sufficient historical data."""
        user = User.objects.create_user(username='testuser', password='testpass')
        workspace = Workspace.objects.create(name='Test Workspace', owner=user)
        task_list = TaskList.objects.create(name='Test List', workspace=workspace, created_by=user)
        task = Task.objects.create(title='Test Task', task_list=task_list, created_by=user, priority='P3')

        # Create 5 historical entries with similar durations
        for i in range(5):
            TimeEntry.objects.create(
                user=user,
                task=task,
                project=task_list,
                start_time=timezone.now() - timedelta(days=i+1),
                end_time=timezone.now() - timedelta(days=i+1, hours=-2),
                duration=timedelta(hours=2),
                is_running=False,
            )

        # Get suggestion
        suggestion = TimeSuggestion.get_suggestion(user, task)

        assert suggestion is not None
        assert suggestion['count'] >= 3
        assert suggestion['duration'] == timedelta(hours=2)

    def test_no_suggestion_with_insufficient_history(self):
        """Test that no suggestion is returned with insufficient data."""
        user = User.objects.create_user(username='testuser', password='testpass')
        workspace = Workspace.objects.create(name='Test Workspace', owner=user)
        task_list = TaskList.objects.create(name='Test List', workspace=workspace, created_by=user)
        task = Task.objects.create(title='Test Task', task_list=task_list, created_by=user, priority='P3')

        # Create only 2 historical entries (less than minimum)
        for i in range(2):
            TimeEntry.objects.create(
                user=user,
                task=task,
                project=task_list,
                start_time=timezone.now() - timedelta(days=i+1),
                end_time=timezone.now() - timedelta(days=i+1, hours=-2),
                duration=timedelta(hours=2),
                is_running=False,
            )

        # Get suggestion
        suggestion = TimeSuggestion.get_suggestion(user, task)

        # Should return None due to insufficient data
        assert suggestion is None


@pytest.mark.django_db
class TestTimeGoals:
    """Test time goal tracking and progress."""

    def test_time_goal_progress_calculation(self):
        """Test calculating progress towards a time goal."""
        user = User.objects.create_user(username='testuser', password='testpass')
        workspace = Workspace.objects.create(name='Test Workspace', owner=user)
        task_list = TaskList.objects.create(name='Test List', workspace=workspace, created_by=user)
        task = Task.objects.create(title='Test Task', task_list=task_list, created_by=user, priority='P3')

        # Create time goal: 10 hours target
        goal = TimeGoal.objects.create(
            user=user,
            task=task,
            goal_type='total',
            target_duration=timedelta(hours=10),
            is_active=True,
        )

        # Create some completed time entries: 6 hours total
        for i in range(3):
            TimeEntry.objects.create(
                user=user,
                task=task,
                project=task_list,
                start_time=timezone.now() - timedelta(days=i+1),
                end_time=timezone.now() - timedelta(days=i+1, hours=-2),
                duration=timedelta(hours=2),
                is_running=False,
            )

        # Get progress
        progress = goal.get_progress()
        percentage = goal.get_percentage_complete()

        assert progress == timedelta(hours=6)
        assert percentage == 60.0
        assert goal.is_overbudget() is False

    def test_time_goal_overbudget_detection(self):
        """Test detecting when time exceeds budget."""
        user = User.objects.create_user(username='testuser', password='testpass')
        workspace = Workspace.objects.create(name='Test Workspace', owner=user)
        task_list = TaskList.objects.create(name='Test List', workspace=workspace, created_by=user)
        task = Task.objects.create(title='Test Task', task_list=task_list, created_by=user, priority='P3')

        # Create time goal: 5 hours target
        goal = TimeGoal.objects.create(
            user=user,
            task=task,
            goal_type='total',
            target_duration=timedelta(hours=5),
            is_active=True,
        )

        # Create time entries totaling 6 hours (over budget)
        for i in range(3):
            TimeEntry.objects.create(
                user=user,
                task=task,
                project=task_list,
                start_time=timezone.now() - timedelta(days=i+1),
                end_time=timezone.now() - timedelta(days=i+1, hours=-2),
                duration=timedelta(hours=2),
                is_running=False,
            )

        # Check if overbudget
        assert goal.is_overbudget() is True
        assert goal.get_percentage_complete() == 120.0


@pytest.mark.django_db
class TestBillableRates:
    """Test billable rate calculations and revenue tracking."""

    def test_revenue_calculation(self):
        """Test calculating revenue from billable time entry."""
        user = User.objects.create_user(username='testuser', password='testpass')
        workspace = Workspace.objects.create(name='Test Workspace', owner=user)
        task_list = TaskList.objects.create(name='Test List', workspace=workspace, created_by=user)
        task = Task.objects.create(title='Test Task', task_list=task_list, created_by=user, priority='P3')

        # Create billable time entry: 2 hours at $50/hour
        time_entry = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task_list,
            duration=timedelta(hours=2),
            is_billable=True,
            billable_rate=50.00,
            currency='USD',
            is_running=False,
        )

        # Calculate revenue
        duration_hours = time_entry.duration.total_seconds() / 3600
        revenue = duration_hours * float(time_entry.billable_rate)

        assert revenue == 100.00

    def test_user_default_billable_rate(self):
        """Test applying user's default billable rate."""
        user = User.objects.create_user(username='testuser', password='testpass')

        # Create user preferences with default rate
        prefs = UserTimePreferences.objects.create(
            user=user,
            default_billable_rate=75.00,
            default_currency='USD',
        )

        assert prefs.default_billable_rate == 75.00
        assert prefs.default_currency == 'USD'
