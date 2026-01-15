"""
Tests for quick date action functionality.
"""
import pytest
from datetime import date, timedelta
from django.urls import reverse
from tasks.models import Task


@pytest.mark.django_db
class TestTaskQuickDateView:
    """Test suite for TaskQuickDateView."""

    def test_today_action_sets_due_date_to_today(self, client, user, task_list):
        """Test that 'today' action sets task due_date to current date."""
        client.force_login(user)

        # Create task without due date
        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        url = reverse('tasks:task-quick-date', kwargs={'pk': task.id})
        response = client.post(url, {'action': 'today'}, HTTP_HX_REQUEST='true')

        assert response.status_code == 200
        assert 'HX-Trigger' in response

        # Reload task and check due_date
        task.refresh_from_db()
        assert task.due_date == date.today()

    def test_tomorrow_action_sets_due_date_to_tomorrow(self, client, user, task_list):
        """Test that 'tomorrow' action sets task due_date to tomorrow."""
        client.force_login(user)

        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        url = reverse('tasks:task-quick-date', kwargs={'pk': task.id})
        response = client.post(url, {'action': 'tomorrow'}, HTTP_HX_REQUEST='true')

        assert response.status_code == 200

        task.refresh_from_db()
        assert task.due_date == date.today() + timedelta(days=1)

    def test_clear_action_removes_due_date(self, client, user, task_list):
        """Test that 'clear' action removes task due_date."""
        client.force_login(user)

        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=date.today(),
            status='active'
        )

        url = reverse('tasks:task-quick-date', kwargs={'pk': task.id})
        response = client.post(url, {'action': 'clear'}, HTTP_HX_REQUEST='true')

        assert response.status_code == 200

        task.refresh_from_db()
        assert task.due_date is None
