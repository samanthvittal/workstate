"""
Tests for task views with tag functionality.
"""
import pytest
from django.urls import reverse
from tasks.models import Task, Tag


@pytest.mark.django_db
class TestTaskCreateViewWithTags:
    """Test suite for TaskCreateView with tag handling."""

    def test_task_creation_with_tags(self, client, user, task_list, workspace):
        """Test that tasks can be created with tags."""
        client.force_login(user)

        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})
        data = {
            'title': 'Test Task',
            'priority': 'P2',
            'status': 'active',
            'tags_input': 'work, urgent, client-a',
        }

        response = client.post(url, data)

        # Should redirect after successful creation
        assert response.status_code == 302

        # Check task was created
        task = Task.objects.get(title='Test Task')
        assert task.tags.count() == 3

        # Check tags were created in correct workspace
        assert Tag.objects.filter(workspace=workspace, name='work').exists()
        assert Tag.objects.filter(workspace=workspace, name='urgent').exists()
        assert Tag.objects.filter(workspace=workspace, name='client-a').exists()

    def test_task_creation_reuses_existing_tags(self, client, user, task_list, workspace):
        """Test that existing tags are reused when creating tasks."""
        client.force_login(user)

        # Create existing tag
        existing_tag = Tag.objects.create(name='work', workspace=workspace, created_by=user)

        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})
        data = {
            'title': 'Test Task',
            'priority': 'P2',
            'status': 'active',
            'tags_input': 'work, urgent',  # 'work' already exists
        }

        response = client.post(url, data)

        # Should redirect after successful creation
        assert response.status_code == 302

        # Check task was created
        task = Task.objects.get(title='Test Task')
        assert task.tags.count() == 2

        # Check that 'work' tag was reused (not duplicated)
        assert Tag.objects.filter(workspace=workspace, name='work').count() == 1
        assert existing_tag in task.tags.all()

    def test_task_creation_without_tags(self, client, user, task_list):
        """Test that tasks can be created without tags."""
        client.force_login(user)

        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})
        data = {
            'title': 'Test Task Without Tags',
            'priority': 'P2',
            'status': 'active',
            'tags_input': '',  # No tags
        }

        response = client.post(url, data)

        # Should redirect after successful creation
        assert response.status_code == 302

        # Check task was created without tags
        task = Task.objects.get(title='Test Task Without Tags')
        assert task.tags.count() == 0


@pytest.mark.django_db
class TestTaskUpdateViewWithTags:
    """Test suite for TaskUpdateView with tag handling."""

    def test_task_update_with_tags(self, client, user, task_list, workspace):
        """Test that task tags can be updated."""
        client.force_login(user)

        # Create task without tags
        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user
        )

        url = reverse('tasks:task-edit', kwargs={'pk': task.pk})
        data = {
            'title': 'Updated Task',
            'priority': 'P2',
            'status': 'active',
            'tags_input': 'work, urgent',
        }

        response = client.post(url, data)

        # Should redirect after successful update
        assert response.status_code == 302

        # Check task was updated with tags
        task.refresh_from_db()
        assert task.title == 'Updated Task'
        assert task.tags.count() == 2
        assert Tag.objects.filter(workspace=workspace, name='work').exists()
        assert Tag.objects.filter(workspace=workspace, name='urgent').exists()

    def test_task_update_replaces_existing_tags(self, client, user, task_list, workspace):
        """Test that updating task tags replaces (not appends to) existing tags."""
        client.force_login(user)

        # Create task with initial tags
        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user
        )
        tag1 = Tag.objects.create(name='old-tag', workspace=workspace, created_by=user)
        task.tags.add(tag1)

        url = reverse('tasks:task-edit', kwargs={'pk': task.pk})
        data = {
            'title': 'Test Task',
            'priority': 'P2',
            'status': 'active',
            'tags_input': 'new-tag',  # Replace with new tag
        }

        response = client.post(url, data)

        # Should redirect after successful update
        assert response.status_code == 302

        # Check task tags were replaced
        task.refresh_from_db()
        assert task.tags.count() == 1
        assert not task.tags.filter(name='old-tag').exists()
        assert task.tags.filter(name='new-tag').exists()

    def test_task_update_can_remove_all_tags(self, client, user, task_list, workspace):
        """Test that all tags can be removed from a task."""
        client.force_login(user)

        # Create task with tags
        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user
        )
        tag1 = Tag.objects.create(name='tag1', workspace=workspace, created_by=user)
        task.tags.add(tag1)

        url = reverse('tasks:task-edit', kwargs={'pk': task.pk})
        data = {
            'title': 'Test Task',
            'priority': 'P2',
            'status': 'active',
            'tags_input': '',  # Remove all tags
        }

        response = client.post(url, data)

        # Should redirect after successful update
        assert response.status_code == 302

        # Check all tags were removed
        task.refresh_from_db()
        assert task.tags.count() == 0


@pytest.mark.django_db
class TestTaskListViewTagFiltering:
    """Test suite for TaskListView tag filtering."""

    def test_task_list_filtered_by_tag(self, client, user, task_list, workspace):
        """Test that tasks can be filtered by tag."""
        client.force_login(user)

        # Create tasks with different tags
        task1 = Task.objects.create(title='Task 1', priority='P2', task_list=task_list, created_by=user)
        task2 = Task.objects.create(title='Task 2', priority='P2', task_list=task_list, created_by=user)
        task3 = Task.objects.create(title='Task 3', priority='P2', task_list=task_list, created_by=user)

        tag_work = Tag.objects.create(name='work', workspace=workspace, created_by=user)
        tag_urgent = Tag.objects.create(name='urgent', workspace=workspace, created_by=user)

        task1.tags.add(tag_work)
        task2.tags.add(tag_work, tag_urgent)
        task3.tags.add(tag_urgent)

        # Test queryset filtering directly (avoid full page rendering in test)
        from tasks.views import TaskListView
        view = TaskListView()
        view.request = type('Request', (), {'user': user, 'GET': {'tag': 'work'}})()

        queryset = view.get_queryset()
        task_ids = list(queryset.values_list('id', flat=True))

        assert task1.id in task_ids
        assert task2.id in task_ids
        assert task3.id not in task_ids

    def test_task_list_tag_filter_case_insensitive(self, client, user, task_list, workspace):
        """Test that tag filtering is case-insensitive."""
        client.force_login(user)

        # Create task with lowercase tag
        task = Task.objects.create(title='Task 1', priority='P2', task_list=task_list, created_by=user)
        tag = Tag.objects.create(name='work', workspace=workspace, created_by=user)
        task.tags.add(tag)

        # Test queryset filtering directly with uppercase tag name
        from tasks.views import TaskListView
        view = TaskListView()
        view.request = type('Request', (), {'user': user, 'GET': {'tag': 'WORK'}})()

        queryset = view.get_queryset()
        task_ids = list(queryset.values_list('id', flat=True))

        assert task.id in task_ids

    def test_task_list_current_tag_in_context(self, client, user):
        """Test that current_tag is added to context when filtering."""
        client.force_login(user)

        url = reverse('tasks:task-list-all')
        response = client.get(url, {'tag': 'work'})

        assert response.status_code == 200
        assert 'current_tag' in response.context
        assert response.context['current_tag'] == 'work'


@pytest.mark.django_db
class TestTagWorkspaceIsolation:
    """Test suite for tag workspace isolation."""

    def test_tags_isolated_by_workspace(self, client, user, user2, workspace, workspace2):
        """Test that tags are isolated by workspace."""
        client.force_login(user)

        # Create task list in user's workspace
        from tasks.models import TaskList
        task_list1 = TaskList.objects.create(
            name='List 1',
            workspace=workspace,
            created_by=user
        )

        # Create task with tag in workspace 1
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list1.id})
        data = {
            'title': 'Task in Workspace 1',
            'priority': 'P2',
            'status': 'active',
            'tags_input': 'shared-name',
        }
        response = client.post(url, data)

        # Tag should exist in workspace 1
        assert Tag.objects.filter(workspace=workspace, name='shared-name').exists()

        # Create task list in user2's workspace
        client.force_login(user2)
        task_list2 = TaskList.objects.create(
            name='List 2',
            workspace=workspace2,
            created_by=user2
        )

        # Create task with same tag name in workspace 2
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list2.id})
        data = {
            'title': 'Task in Workspace 2',
            'priority': 'P2',
            'status': 'active',
            'tags_input': 'shared-name',
        }
        response = client.post(url, data)

        # Tag should also exist in workspace 2 (separate instance)
        assert Tag.objects.filter(workspace=workspace2, name='shared-name').exists()

        # Should have 2 separate tag instances with same name
        assert Tag.objects.filter(name='shared-name').count() == 2
