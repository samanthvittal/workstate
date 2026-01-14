"""
Integration tests for end-to-end task creation and editing workflows.
"""
import pytest
from django.urls import reverse
from tasks.models import Task


@pytest.mark.django_db
class TestTaskCreationWorkflow:
    """Integration tests for end-to-end task creation workflow."""

    def test_end_to_end_task_creation_workflow(self, client, user, task_list):
        """Test complete task creation workflow from form load to task saved."""
        client.force_login(user)
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})

        # Step 1: Load the form
        response = client.get(url)
        assert response.status_code == 200
        assert 'name="title"' in response.content.decode()

        # Step 2: Submit valid task data
        response = client.post(url, {
            'title': 'Integration Test Task',
            'description': 'This is an integration test',
            'due_date': '2026-12-31',
            'due_time': '15:00',
            'priority': 'P1',
        }, follow=True)

        # Step 3: Verify redirect to same URL with success
        assert response.status_code == 200

        # Step 4: Verify task was created in database
        task = Task.objects.filter(title='Integration Test Task').first()
        assert task is not None
        assert task.task_list == task_list
        assert task.created_by == user
        assert task.priority == 'P1'
        assert task.description == 'This is an integration test'
        assert str(task.due_date) == '2026-12-31'

    def test_multiple_task_creation_in_sequence(self, client, user, task_list):
        """Test creating multiple tasks in sequence using the same form."""
        client.force_login(user)
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})

        # Create first task
        response = client.post(url, {
            'title': 'First Task',
            'priority': 'P1',
        }, follow=True)
        assert response.status_code == 200

        # Create second task
        response = client.post(url, {
            'title': 'Second Task',
            'priority': 'P2',
        }, follow=True)
        assert response.status_code == 200

        # Create third task
        response = client.post(url, {
            'title': 'Third Task',
            'priority': 'P3',
        }, follow=True)
        assert response.status_code == 200

        # Verify all three tasks exist
        tasks = Task.objects.filter(task_list=task_list).order_by('created_at')
        assert tasks.count() == 3
        assert tasks[0].title == 'First Task'
        assert tasks[1].title == 'Second Task'
        assert tasks[2].title == 'Third Task'

    def test_task_creation_with_validation_errors(self, client, user, task_list):
        """Test that validation errors are displayed properly in integration context."""
        client.force_login(user)
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})

        # Submit task with missing title
        response = client.post(url, {
            'title': '',
            'priority': 'P1',
        })

        assert response.status_code == 200
        content = response.content.decode()
        # Form should display with error message
        assert 'name="title"' in content

        # Verify no task was created
        assert Task.objects.filter(task_list=task_list).count() == 0

    def test_success_message_display_after_task_creation(self, client, user, task_list):
        """Test that success message is displayed after task creation."""
        client.force_login(user)
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})

        # Submit valid task
        response = client.post(url, {
            'title': 'Success Message Test',
            'priority': 'P2',
        }, follow=True)

        assert response.status_code == 200
        # Check for success message in response
        messages = list(response.context['messages'])
        assert len(messages) > 0
        assert 'success' in str(messages[0].tags).lower() or 'Task created' in str(messages[0])


@pytest.mark.django_db
class TestTaskEditingWorkflow:
    """Integration tests for end-to-end task editing workflow."""

    @pytest.fixture
    def editing_task(self, user, task_list):
        """Create a task with specific data for editing tests."""
        return Task.objects.create(
            title='Original Task Title',
            description='Original description',
            priority='P3',
            task_list=task_list,
            created_by=user
        )

    def test_end_to_end_task_editing_workflow(self, client, user, editing_task):
        """Test complete task editing workflow from form load to task updated."""
        client.force_login(user)
        url = reverse('tasks:task-edit', kwargs={'pk': editing_task.id})

        # Step 1: Load the edit form via HTMX
        response = client.get(url, HTTP_HX_REQUEST='true')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Original Task Title' in content
        assert 'Original description' in content

        # Step 2: Submit updated task data
        response = client.post(url, {
            'title': 'Updated Task Title',
            'description': 'Updated description',
            'priority': 'P1',
            'status': 'completed',
        }, HTTP_HX_REQUEST='true')

        # Step 3: Verify task was updated in database
        editing_task.refresh_from_db()
        assert editing_task.title == 'Updated Task Title'
        assert editing_task.description == 'Updated description'
        assert editing_task.priority == 'P1'
        assert editing_task.status == 'completed'

    def test_task_update_with_all_field_changes(self, client, user, editing_task):
        """Test updating task with changes to all fields."""
        client.force_login(user)
        url = reverse('tasks:task-edit', kwargs={'pk': editing_task.id})

        # Update all fields
        response = client.post(url, {
            'title': 'Completely Updated Task',
            'description': 'Brand new description with markdown **support**',
            'due_date': '2026-06-15',
            'due_time': '14:30',
            'priority': 'P2',
            'status': 'completed',
        })

        # Verify all fields were updated
        editing_task.refresh_from_db()
        assert editing_task.title == 'Completely Updated Task'
        assert editing_task.description == 'Brand new description with markdown **support**'
        assert str(editing_task.due_date) == '2026-06-15'
        assert str(editing_task.due_time) == '14:30:00'
        assert editing_task.priority == 'P2'
        assert editing_task.status == 'completed'

    def test_task_edit_with_validation_errors(self, client, user, editing_task):
        """Test that validation errors are handled properly during task edit."""
        client.force_login(user)
        url = reverse('tasks:task-edit', kwargs={'pk': editing_task.id})

        # Submit update with invalid data (empty title)
        response = client.post(url, {
            'title': '',
            'priority': 'P1',
        }, HTTP_HX_REQUEST='true')

        assert response.status_code == 200
        # Form should be redisplayed with errors
        content = response.content.decode()
        assert 'name="title"' in content

        # Verify task was NOT updated
        editing_task.refresh_from_db()
        assert editing_task.title == 'Original Task Title'


@pytest.mark.django_db
class TestWorkspaceIsolation:
    """Integration tests for workspace isolation and permissions."""

    def test_cannot_create_task_in_another_users_task_list(self, client, user, task_list2):
        """Test that users cannot create tasks in task lists they don't own."""
        client.force_login(user)
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list2.id})

        # Attempt to create task in user2's task list
        response = client.post(url, {
            'title': 'Unauthorized Task',
            'priority': 'P1',
        })

        # Should be forbidden
        assert response.status_code == 403

        # Verify no task was created
        assert Task.objects.filter(title='Unauthorized Task').count() == 0

    def test_cannot_edit_another_users_task(self, client, user, task):
        """Test that users cannot edit tasks in task lists they don't own."""
        # Create another user and their task
        from django.contrib.auth.models import User
        from accounts.models import Workspace
        from tasks.models import TaskList

        user2 = User.objects.create_user(username='user2', email='user2@example.com', password='test123')
        workspace2 = Workspace.objects.create(name='User 2 Workspace', owner=user2)
        task_list2 = TaskList.objects.create(name='User 2 List', workspace=workspace2, created_by=user2)
        task2 = Task.objects.create(title='User 2 Task', priority='P1', task_list=task_list2, created_by=user2)

        client.force_login(user)
        url = reverse('tasks:task-edit', kwargs={'pk': task2.id})

        # Attempt to edit user2's task
        response = client.get(url)

        # Should return 404 (task not found in user's workspaces)
        assert response.status_code == 404


@pytest.mark.django_db
class TestURLConfiguration:
    """Integration tests for URL routing and namespacing."""

    def test_url_namespacing_for_task_create(self, task_list):
        """Test that URL namespacing works correctly for task creation."""
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})
        expected = f'/tasklist/{task_list.id}/tasks/create/'
        assert url == expected

    def test_url_namespacing_for_task_edit(self, task):
        """Test that URL namespacing works correctly for task editing."""
        url = reverse('tasks:task-edit', kwargs={'pk': task.id})
        expected = f'/tasks/{task.id}/edit/'
        assert url == expected
