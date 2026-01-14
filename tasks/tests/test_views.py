"""
Tests for task views.
"""
import pytest
from django.urls import reverse
from tasks.models import Task


@pytest.mark.django_db
class TestTaskCreateView:
    """Test suite for TaskCreateView."""

    def test_create_view_requires_authentication(self, client, task_list):
        """Test that TaskCreateView requires authentication."""
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})
        response = client.get(url)

        # Should redirect to login page
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_create_view_requires_task_list_access(self, client, user, task_list2):
        """Test that TaskCreateView requires task list access."""
        client.force_login(user)
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list2.id})
        response = client.get(url)

        # Should return 403 Forbidden
        assert response.status_code == 403

    def test_create_view_saves_with_correct_task_list_and_created_by(self, client, user, task_list):
        """Test that TaskCreateView saves task with correct task list and created_by."""
        client.force_login(user)
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})

        response = client.post(url, {
            'title': 'New Task',
            'priority': 'P2',
            'description': 'Test description',
        })

        # Should redirect back to the form
        assert response.status_code == 302

        # Verify task was created
        task = Task.objects.filter(title='New Task').first()
        assert task is not None
        assert task.task_list == task_list
        assert task.created_by == user
        assert task.priority == 'P2'


@pytest.mark.django_db
class TestTaskUpdateView:
    """Test suite for TaskUpdateView."""

    def test_update_view_requires_authentication(self, client, task):
        """Test that TaskUpdateView requires authentication."""
        url = reverse('tasks:task-edit', kwargs={'pk': task.id})
        response = client.get(url)

        # Should redirect to login page
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_update_view_verifies_task_ownership_via_task_list(self, client, user, task):
        """Test that TaskUpdateView verifies task ownership via task list."""
        # Create another user's task
        from django.contrib.auth.models import User
        from accounts.models import Workspace
        from tasks.models import TaskList

        user2 = User.objects.create_user(username='user2', email='user2@example.com', password='test123')
        workspace2 = Workspace.objects.create(name='User 2 Workspace', owner=user2)
        task_list2 = TaskList.objects.create(name='User 2 List', workspace=workspace2, created_by=user2)
        other_task = Task.objects.create(title='Other Task', priority='P1', task_list=task_list2, created_by=user2)

        client.force_login(user)
        url = reverse('tasks:task-edit', kwargs={'pk': other_task.id})
        response = client.get(url)

        # Should return 404 (task not found in user's workspaces)
        assert response.status_code == 404

    def test_htmx_request_returns_partial_template(self, client, user, task):
        """Test that HTMX request returns partial template."""
        client.force_login(user)
        url = reverse('tasks:task-edit', kwargs={'pk': task.id})

        # Make HTMX request
        response = client.get(url, HTTP_HX_REQUEST='true')

        assert response.status_code == 200
        # Verify it returns a partial template (should not have full page structure)
        # Check for form presence without full page elements
        assert b'<form' in response.content
