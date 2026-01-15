"""
Tests for Task manager methods and due date model methods.
"""
import pytest
from datetime import date, timedelta
from tasks.models import Task


@pytest.mark.django_db
class TestTaskManagerDueDateMethods:
    """Test suite for TaskManager due date query methods."""

    def test_upcoming_returns_tasks_in_next_7_days_by_default(self, user, task_list):
        """Test that upcoming() returns tasks due in next 7 days (excluding today)."""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        day_7 = today + timedelta(days=7)
        day_8 = today + timedelta(days=8)

        # Create tasks with various due dates
        task_tomorrow = Task.objects.create(
            title='Task Tomorrow',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=tomorrow,
            status='active'
        )
        task_day7 = Task.objects.create(
            title='Task Day 7',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=day_7,
            status='active'
        )
        task_day8 = Task.objects.create(
            title='Task Day 8',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=day_8,
            status='active'
        )
        task_today = Task.objects.create(
            title='Task Today',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today,
            status='active'
        )

        # Get upcoming tasks filtered by this test's task list
        upcoming = Task.objects.upcoming().filter(task_list=task_list)

        # Should include tomorrow and day 7, but not today or day 8
        assert task_tomorrow in upcoming
        assert task_day7 in upcoming
        assert task_day8 not in upcoming
        assert task_today not in upcoming
        assert upcoming.count() == 2

    def test_upcoming_respects_days_parameter(self, user, task_list):
        """Test that upcoming() respects custom days parameter."""
        today = date.today()
        day_14 = today + timedelta(days=14)
        day_15 = today + timedelta(days=15)

        # Create tasks
        task_day14 = Task.objects.create(
            title='Task Day 14',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=day_14,
            status='active'
        )
        task_day15 = Task.objects.create(
            title='Task Day 15',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=day_15,
            status='active'
        )

        # Get upcoming tasks for 14 days
        upcoming_14 = Task.objects.upcoming(days=14)

        # Should include day 14 but not day 15
        assert task_day14 in upcoming_14
        assert task_day15 not in upcoming_14

        # Get upcoming tasks for 30 days
        upcoming_30 = Task.objects.upcoming(days=30)

        # Should include both
        assert task_day14 in upcoming_30
        assert task_day15 in upcoming_30

    def test_no_due_date_returns_tasks_without_due_dates(self, user, task_list):
        """Test that no_due_date() returns only active tasks with no due date."""
        today = date.today()

        # Create tasks
        task_with_due_date = Task.objects.create(
            title='Task With Date',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today,
            status='active'
        )
        task_no_date = Task.objects.create(
            title='Task No Date',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        task_completed_no_date = Task.objects.create(
            title='Completed No Date',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='completed'
        )

        # Get tasks without due dates filtered by this test's task list
        no_due_date = Task.objects.no_due_date().filter(task_list=task_list)

        # Should only include active task without due date
        assert task_no_date in no_due_date
        assert task_with_due_date not in no_due_date
        assert task_completed_no_date not in no_due_date
        assert no_due_date.count() == 1


@pytest.mark.django_db
class TestTaskDueDateModelMethods:
    """Test suite for Task model due date helper methods."""

    def test_get_due_status_returns_correct_status(self, user, task_list):
        """Test that get_due_status() returns correct status strings."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        # Overdue task
        task_overdue = Task.objects.create(
            title='Overdue Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=yesterday,
            status='active'
        )
        assert task_overdue.get_due_status() == 'overdue'

        # Due today task
        task_today = Task.objects.create(
            title='Today Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today,
            status='active'
        )
        assert task_today.get_due_status() == 'due_today'

        # Upcoming task
        task_upcoming = Task.objects.create(
            title='Upcoming Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=tomorrow,
            status='active'
        )
        assert task_upcoming.get_due_status() == 'upcoming'

        # No due date task
        task_no_date = Task.objects.create(
            title='No Date Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        assert task_no_date.get_due_status() == 'no_due_date'

    def test_get_due_status_color_returns_correct_colors(self, user, task_list):
        """Test that get_due_status_color() returns correct Tailwind color classes."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        # Overdue task - red
        task_overdue = Task.objects.create(
            title='Overdue Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=yesterday,
            status='active'
        )
        assert task_overdue.get_due_status_color() == 'red'

        # Due today task - yellow
        task_today = Task.objects.create(
            title='Today Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today,
            status='active'
        )
        assert task_today.get_due_status_color() == 'yellow'

        # Upcoming task - green
        task_upcoming = Task.objects.create(
            title='Upcoming Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=tomorrow,
            status='active'
        )
        assert task_upcoming.get_due_status_color() == 'green'

        # No due date task - gray
        task_no_date = Task.objects.create(
            title='No Date Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        assert task_no_date.get_due_status_color() == 'gray'
