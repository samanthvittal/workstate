"""
Tests for UI rendering components (Task Group 4: Frontend UI Components & HTMX Integration).

This test file covers:
- Interactive checkbox rendering with HTMX attributes
- Completed task visual styling (strikethrough, color)
- Status filter buttons in sidebar
- Sidebar count format "X of Y complete"

Limited to 4 focused tests as per Task Group 4.1 requirements.
"""
import pytest
from django.urls import reverse
from tasks.models import Task


@pytest.mark.django_db
class TestInteractiveCheckboxRendering:
    """Test suite for interactive checkbox HTMX rendering."""

    def test_task_card_renders_with_interactive_checkbox(self, client, user, task_list):
        """Test that task card renders with interactive checkbox containing HTMX attributes."""
        # Create a task
        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        # Login and request task list view
        client.force_login(user)
        url = reverse('tasks:task-list-all')
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Verify checkbox is present and NOT disabled
        assert 'type="checkbox"' in content
        assert 'disabled' not in content or content.count('disabled') == 0

        # Verify HTMX attributes are present
        assert 'hx-post' in content
        assert f'/tasks/{task.id}/toggle-status/' in content
        assert 'hx-target' in content
        assert f'task-{task.id}' in content
        assert 'hx-swap' in content
        assert 'outerHTML' in content

        # Verify cursor-pointer class for visual feedback
        assert 'cursor-pointer' in content


@pytest.mark.django_db
class TestCompletedTaskVisualStyling:
    """Test suite for completed task visual styling."""

    def test_completed_task_displays_with_strikethrough_styling(self, client, user, task_list):
        """Test that completed tasks display with strikethrough and gray text."""
        # Create a completed task
        task = Task.objects.create(
            title='Completed Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        task.mark_complete()
        task.refresh_from_db()

        # Login and request task list view with status=all to see completed tasks
        client.force_login(user)
        url = reverse('tasks:task-list-all')
        response = client.get(url, {'status': 'all'})

        assert response.status_code == 200
        content = response.content.decode()

        # Verify strikethrough class is present
        assert 'line-through' in content
        assert 'text-gray-500' in content

        # Verify checkbox is checked
        assert 'checked' in content

        # Verify completion timestamp is displayed
        assert 'Completed' in content


@pytest.mark.django_db
class TestStatusFilterButtons:
    """Test suite for status filter buttons in sidebar."""

    def test_status_filter_buttons_render_correctly_in_sidebar(self, client, user, workspace, task_list):
        """Test that status filter buttons render with correct active state styling."""
        # Create tasks with different statuses
        active_task = Task.objects.create(
            title='Active Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        completed_task = Task.objects.create(
            title='Completed Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        completed_task.mark_complete()

        # Login and request task list view
        client.force_login(user)
        url = reverse('tasks:task-list-all')
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Verify filter buttons are present
        assert 'Active' in content
        assert 'Completed' in content
        assert 'All' in content

        # Verify status filter links are present
        assert '?status=active' in content
        assert '?status=completed' in content
        assert '?status=all' in content

        # Verify active state styling is applied
        assert 'bg-blue-600' in content
        assert 'text-white' in content

        # Test with completed filter
        response = client.get(url, {'status': 'completed'})
        assert response.status_code == 200
        content = response.content.decode()

        # Verify current_status_filter is passed to context
        assert response.context['current_status_filter'] == 'completed'


@pytest.mark.django_db
class TestSidebarCountFormat:
    """Test suite for sidebar count format."""

    def test_sidebar_counts_display_in_x_of_y_complete_format(self, client, user, workspace, task_list):
        """Test that sidebar counts display in 'X of Y complete' format."""
        # Create multiple tasks
        for i in range(5):
            Task.objects.create(
                title=f'Active Task {i}',
                priority='P2',
                task_list=task_list,
                created_by=user,
                status='active'
            )

        # Mark 3 as completed
        completed_tasks = Task.objects.filter(task_list=task_list)[:3]
        for task in completed_tasks:
            task.mark_complete()

        # Login and request task list view
        client.force_login(user)
        url = reverse('tasks:task-list-all')
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Verify "X of Y complete" format is present
        assert 'of' in content
        assert 'complete' in content

        # Verify counts are correct in context
        assert response.context['completed_count'] == 3
        assert response.context['active_count'] == 2

        # Total should be 5 (not including archived)
        total_count = response.context['completed_count'] + response.context['active_count']
        assert total_count == 5
