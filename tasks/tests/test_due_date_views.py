"""
Tests for due date view filtering in TaskListView.
"""
import pytest
from datetime import date, timedelta
from django.urls import reverse
from tasks.models import Task


@pytest.mark.django_db
class TestTaskListViewDueDateFiltering:
    """Test suite for TaskListView due date filtering logic."""

    def test_today_view_returns_only_today_tasks(self, client, user, task_list):
        """Test that view=today query parameter returns only tasks due today."""
        client.force_login(user)
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        # Create tasks
        task_today = Task.objects.create(
            title='Task Due Today',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today,
            status='active'
        )
        task_overdue = Task.objects.create(
            title='Overdue Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=yesterday,
            status='active'
        )
        task_upcoming = Task.objects.create(
            title='Upcoming Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=tomorrow,
            status='active'
        )

        # Request today view
        url = reverse('tasks:task-list-all') + '?view=today'
        response = client.get(url)

        assert response.status_code == 200
        tasks = response.context['tasks']

        # Should only include today's task
        assert task_today in tasks
        assert task_overdue not in tasks
        assert task_upcoming not in tasks

    def test_upcoming_view_respects_days_parameter(self, client, user, task_list):
        """Test that view=upcoming respects the days query parameter."""
        client.force_login(user)
        today = date.today()
        day_5 = today + timedelta(days=5)
        day_10 = today + timedelta(days=10)
        day_15 = today + timedelta(days=15)

        # Create tasks
        task_day5 = Task.objects.create(
            title='Task Day 5',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=day_5,
            status='active'
        )
        task_day10 = Task.objects.create(
            title='Task Day 10',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=day_10,
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

        # Test default 7 days
        url = reverse('tasks:task-list-all') + '?view=upcoming'
        response = client.get(url)
        tasks = response.context['tasks']
        assert task_day5 in tasks
        assert task_day10 not in tasks
        assert task_day15 not in tasks

        # Test 14 days
        url = reverse('tasks:task-list-all') + '?view=upcoming&days=14'
        response = client.get(url)
        tasks = response.context['tasks']
        assert task_day5 in tasks
        assert task_day10 in tasks
        assert task_day15 not in tasks

    def test_context_includes_due_date_counts(self, client, user, task_list):
        """Test that context includes counts for today, overdue, and upcoming tasks."""
        client.force_login(user)
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        # Create tasks
        Task.objects.create(
            title='Task Today 1',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today,
            status='active'
        )
        Task.objects.create(
            title='Task Today 2',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today,
            status='active'
        )
        Task.objects.create(
            title='Overdue Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=yesterday,
            status='active'
        )
        Task.objects.create(
            title='Upcoming Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=tomorrow,
            status='active'
        )

        url = reverse('tasks:task-list-all')
        response = client.get(url)

        assert response.context['today_count'] == 2
        assert response.context['overdue_count'] == 1
        assert response.context['upcoming_count'] == 1
