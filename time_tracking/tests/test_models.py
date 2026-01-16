"""
Focused tests for TimeEntry and TimeGoal models.

Tests cover only critical model behaviors:
- Timer state transitions
- Duration calculation
- Single active timer constraint
- Task association requirement
- Time goal validation
"""
import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from time_tracking.models import (
    TimeEntry,
    TimeGoal,
    UserTimePreferences,
    PomodoroSession,
    TimeEntryTag
)
from tasks.models import Task, TaskList, Tag
from accounts.models import Workspace


@pytest.mark.django_db
class TestTimeEntryModel:
    """Test critical TimeEntry model behaviors."""

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

    def test_time_entry_requires_task(self, user):
        """Test that task is required for time entries."""
        time_entry = TimeEntry(
            user=user,
            duration=timedelta(hours=1)
        )

        with pytest.raises(ValidationError) as exc_info:
            time_entry.save()

        assert 'task' in str(exc_info.value).lower()

    def test_single_active_timer_constraint(self, user, task, task_list):
        """Test that only one timer can be running per user."""
        # Create first running timer
        timer1 = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task_list,
            start_time=timezone.now(),
            duration=timedelta(0),
            is_running=True
        )

        # Create second task for second timer
        task2 = Task.objects.create(
            title='Second Task',
            priority='P3',
            task_list=task_list,
            created_by=user
        )

        # Attempt to create second running timer
        timer2 = TimeEntry(
            user=user,
            task=task2,
            project=task_list,
            start_time=timezone.now(),
            duration=timedelta(0),
            is_running=True
        )

        with pytest.raises(ValidationError) as exc_info:
            timer2.save()

        assert 'one timer' in str(exc_info.value).lower()

    def test_timer_stop_calculates_duration(self, user, task, task_list):
        """Test that stopping timer correctly calculates duration."""
        start = timezone.now() - timedelta(hours=2)
        timer = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task_list,
            start_time=start,
            duration=timedelta(0),
            is_running=True
        )

        # Stop timer
        end = timezone.now()
        timer.stop(end_time=end)

        # Reload from database
        timer.refresh_from_db()

        assert timer.is_running is False
        assert timer.end_time == end
        assert timer.duration == end - start

    def test_duration_calculation_method(self, user, task, task_list):
        """Test calculate_duration method."""
        start = timezone.now() - timedelta(hours=1, minutes=30)
        end = timezone.now()

        timer = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task_list,
            start_time=start,
            end_time=end,
            duration=end - start,
            is_running=False
        )

        calculated = timer.calculate_duration()
        assert calculated == end - start

    def test_end_time_after_start_time_validation(self, user, task, task_list):
        """Test that end_time must be after start_time."""
        start = timezone.now()
        end = start - timedelta(hours=1)  # End before start

        timer = TimeEntry(
            user=user,
            task=task,
            project=task_list,
            start_time=start,
            end_time=end,
            duration=timedelta(hours=1),
            is_running=False
        )

        with pytest.raises(ValidationError) as exc_info:
            timer.save()

        assert 'end time' in str(exc_info.value).lower()

    def test_time_rounding_applies_correctly(self, user, task, task_list):
        """Test apply_rounding method with different methods."""
        timer = TimeEntry.objects.create(
            user=user,
            task=task,
            project=task_list,
            duration=timedelta(minutes=23),
            is_running=False
        )

        # Test round up (23 minutes -> 30 minutes)
        rounded_up = timer.apply_rounding(15, 'up')
        assert rounded_up == timedelta(minutes=30)

        # Test round down (23 minutes -> 15 minutes)
        rounded_down = timer.apply_rounding(15, 'down')
        assert rounded_down == timedelta(minutes=15)

        # Test round nearest (23 minutes -> 30 minutes, closer to 30 than 15)
        rounded_nearest = timer.apply_rounding(15, 'nearest')
        assert rounded_nearest == timedelta(minutes=30)

    def test_project_inherited_from_task(self, user, task, task_list):
        """Test that project is automatically inherited from task."""
        timer = TimeEntry.objects.create(
            user=user,
            task=task,
            duration=timedelta(hours=1),
            is_running=False
        )

        # Reload from database
        timer.refresh_from_db()

        assert timer.project == task_list


@pytest.mark.django_db
class TestTimeGoalModel:
    """Test critical TimeGoal model behaviors."""

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

    def test_time_goal_requires_project_or_task(self, user):
        """Test that time goal must have either project or task."""
        goal = TimeGoal(
            user=user,
            goal_type='weekly',
            target_duration=timedelta(hours=40)
        )

        with pytest.raises(ValidationError) as exc_info:
            goal.save()

        assert 'project or a task' in str(exc_info.value).lower()

    def test_time_goal_cannot_have_both_project_and_task(self, user, task_list):
        """Test that time goal cannot have both project and task."""
        task = Task.objects.create(
            title='Test Task',
            priority='P3',
            task_list=task_list,
            created_by=user
        )

        goal = TimeGoal(
            user=user,
            project=task_list,
            task=task,
            goal_type='weekly',
            target_duration=timedelta(hours=40)
        )

        with pytest.raises(ValidationError) as exc_info:
            goal.save()

        assert 'not both' in str(exc_info.value).lower()

    def test_time_goal_progress_calculation(self, user, task_list):
        """Test get_progress method calculates correctly."""
        task = Task.objects.create(
            title='Test Task',
            priority='P3',
            task_list=task_list,
            created_by=user
        )

        # Create time entries
        TimeEntry.objects.create(
            user=user,
            task=task,
            project=task_list,
            start_time=timezone.now() - timedelta(hours=2),
            end_time=timezone.now() - timedelta(hours=1),
            duration=timedelta(hours=1),
            is_running=False
        )

        TimeEntry.objects.create(
            user=user,
            task=task,
            project=task_list,
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now(),
            duration=timedelta(hours=1),
            is_running=False
        )

        # Create goal
        goal = TimeGoal.objects.create(
            user=user,
            project=task_list,
            goal_type='total',
            target_duration=timedelta(hours=10)
        )

        progress = goal.get_progress()
        assert progress == timedelta(hours=2)

        # Test percentage
        percentage = goal.get_percentage_complete()
        assert percentage == 20.0

        # Test is_overbudget
        assert goal.is_overbudget() is False
