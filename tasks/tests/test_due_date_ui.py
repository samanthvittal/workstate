"""
Tests for due date UI rendering.
"""
import pytest
from datetime import date, timedelta
from django.urls import reverse
from tasks.models import Task


@pytest.mark.django_db
class TestDueDateUIRendering:
    """Test suite for due date UI elements."""

    def test_sidebar_renders_with_due_date_counts(self, client, user, task_list):
        """Test that sidebar renders with due date view counts."""
        client.force_login(user)
        today = date.today()

        # Create tasks with different due dates
        Task.objects.create(
            title='Task Today',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today,
            status='active'
        )
        Task.objects.create(
            title='Task Overdue',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today - timedelta(days=1),
            status='active'
        )

        url = reverse('tasks:task-list-all')
        response = client.get(url)

        assert response.status_code == 200
        assert 'today_count' in response.context
        assert 'overdue_count' in response.context
        assert 'upcoming_count' in response.context

    def test_active_view_highlighted_in_context(self, client, user, task_list):
        """Test that active view is set in context for sidebar highlighting."""
        client.force_login(user)

        # Test today view
        url = reverse('tasks:task-list-all') + '?view=today'
        response = client.get(url)
        assert response.context['active_view'] == 'today'

        # Test upcoming view
        url = reverse('tasks:task-list-all') + '?view=upcoming'
        response = client.get(url)
        assert response.context['active_view'] == 'upcoming'

        # Test overdue view
        url = reverse('tasks:task-list-all') + '?view=overdue'
        response = client.get(url)
        assert response.context['active_view'] == 'overdue'

    def test_due_status_label_shows_correct_colors(self, client, user, task_list):
        """Test that due status labels display with correct color context."""
        client.force_login(user)
        today = date.today()

        # Create task due today
        task = Task.objects.create(
            title='Task Today',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today,
            status='active'
        )

        url = reverse('tasks:task-list-all')
        response = client.get(url)

        assert response.status_code == 200
        # Verify due_today method returns True
        assert task.is_due_today() is True
        assert task.get_due_status_color() == 'yellow'
