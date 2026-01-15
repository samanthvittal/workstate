"""
Integration tests for Task Status & Completion feature (Task Group 5).

This test file covers end-to-end user workflows:
- Complete task workflow: mark task complete -> verify positioned at bottom -> verify completed_at set
- Filter workflow: change status filter -> verify preference persists -> verify correct tasks shown
- Bulk complete workflow: mark all complete -> verify all tasks completed -> verify counts updated
- Archive workflow: complete task -> archive -> verify excluded from normal view -> verify in archive view
- Unarchive workflow: unarchive task -> verify restored to normal view
- Keyboard shortcut workflow: tested manually (Alpine.js client-side functionality)

Maximum 6 integration tests as per task requirements.
"""
import pytest
from django.test import Client
from django.urls import reverse
from tasks.models import Task
from accounts.models import UserPreference


@pytest.mark.django_db
class TestCompleteTaskWorkflow:
    """Test complete end-to-end task completion workflow."""

    def test_complete_workflow_marks_task_and_positions_at_bottom(self, user, task_list):
        """Test complete workflow: mark task complete -> verify positioned at bottom -> verify completed_at set."""
        client = Client()
        client.force_login(user)

        # Create multiple active tasks
        task1 = Task.objects.create(
            title='First Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        task2 = Task.objects.create(
            title='Second Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        task3 = Task.objects.create(
            title='Third Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        # Mark task1 as complete via toggle-status endpoint
        url = reverse('tasks:toggle-status', kwargs={'pk': task1.pk})
        response = client.post(url)
        assert response.status_code == 200

        # Refresh task from database
        task1.refresh_from_db()

        # Verify task is completed with timestamp
        assert task1.status == 'completed'
        assert task1.completed_at is not None

        # View task list with 'all' status to see positioning
        list_url = reverse('tasks:task-list-all')
        response = client.get(list_url, {'status': 'all'})
        assert response.status_code == 200

        # Verify task ordering (completed tasks at bottom)
        tasks = list(response.context['tasks'])
        task_ids = [t.id for t in tasks]

        # Active tasks (task2, task3) should come before completed task (task1)
        assert task2.id in task_ids
        assert task3.id in task_ids
        assert task1.id in task_ids

        # Find positions
        task1_pos = task_ids.index(task1.id)
        task2_pos = task_ids.index(task2.id)
        task3_pos = task_ids.index(task3.id)

        # Completed task should be after active tasks
        assert task1_pos > task2_pos
        assert task1_pos > task3_pos


@pytest.mark.django_db
class TestStatusFilterWorkflow:
    """Test status filter persistence workflow."""

    def test_filter_workflow_persists_preference_and_shows_correct_tasks(self, user, task_list):
        """Test filter workflow: change status filter -> verify preference persists -> verify correct tasks shown."""
        client = Client()
        client.force_login(user)

        # Create user preference if not exists
        user_prefs, created = UserPreference.objects.get_or_create(user=user)
        assert user_prefs.default_task_status_filter == 'active'

        # Create active and completed tasks
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

        # Change filter to 'completed'
        url = reverse('tasks:task-list-all')
        response = client.get(url, {'status': 'completed'})
        assert response.status_code == 200

        # Verify preference was persisted
        user_prefs.refresh_from_db()
        assert user_prefs.default_task_status_filter == 'completed'

        # Verify only completed tasks are shown
        tasks = list(response.context['tasks'])
        assert completed_task in tasks
        assert active_task not in tasks

        # Load page again without query parameter (should use saved preference)
        response = client.get(url)
        assert response.status_code == 200

        # Should still show completed filter
        assert response.context['current_status_filter'] == 'completed'
        tasks = list(response.context['tasks'])
        assert completed_task in tasks
        assert active_task not in tasks


@pytest.mark.django_db
class TestBulkCompleteWorkflow:
    """Test bulk complete workflow."""

    def test_bulk_complete_workflow_marks_all_and_updates_counts(self, user, task_list):
        """Test bulk complete workflow: mark all complete -> verify all tasks completed -> verify counts updated."""
        client = Client()
        client.force_login(user)

        # Create multiple active tasks
        tasks = []
        for i in range(5):
            task = Task.objects.create(
                title=f'Task {i+1}',
                priority='P2',
                task_list=task_list,
                created_by=user,
                status='active'
            )
            tasks.append(task)

        # Verify initial state (all active)
        for task in tasks:
            assert task.status == 'active'
            assert task.completed_at is None

        # Execute bulk complete
        url = reverse('tasks:mark-all-complete', kwargs={'pk': task_list.pk})
        response = client.post(url)
        assert response.status_code == 200

        # Refresh all tasks from database
        for task in tasks:
            task.refresh_from_db()
            assert task.status == 'completed'
            assert task.completed_at is not None

        # Verify counts are updated in task list view
        list_url = reverse('tasks:task-list-all')
        response = client.get(list_url, {'status': 'all'})
        assert response.status_code == 200

        # All 5 tasks should be completed
        assert response.context['completed_count'] == 5
        assert response.context['active_count'] == 0


@pytest.mark.django_db
class TestArchiveWorkflow:
    """Test task archive workflow."""

    def test_archive_workflow_removes_from_view_and_shows_in_archive(self, user, task_list):
        """Test archive workflow: complete task -> archive -> verify excluded from normal view -> verify in archive view."""
        client = Client()
        client.force_login(user)

        # Create and complete a task
        task = Task.objects.create(
            title='Task to Archive',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        task.mark_complete()
        task.refresh_from_db()

        # Verify task is visible in normal view initially
        list_url = reverse('tasks:task-list-all')
        response = client.get(list_url, {'status': 'all'})
        assert response.status_code == 200
        tasks = list(response.context['tasks'])
        assert task in tasks

        # Archive the task
        archive_url = reverse('tasks:archive-task', kwargs={'pk': task.pk})
        response = client.post(archive_url)
        assert response.status_code == 200

        # Refresh task from database
        task.refresh_from_db()
        assert task.is_archived is True

        # Verify task is NOT in normal view anymore
        response = client.get(list_url, {'status': 'all'})
        assert response.status_code == 200
        tasks = list(response.context['tasks'])
        assert task not in tasks

        # Verify task IS in archive view
        archive_list_url = reverse('tasks:archived-tasks')
        response = client.get(archive_list_url)
        assert response.status_code == 200
        archived_tasks = list(response.context['tasks'])
        assert task in archived_tasks


@pytest.mark.django_db
class TestUnarchiveWorkflow:
    """Test task unarchive workflow."""

    def test_unarchive_workflow_restores_to_normal_view(self, user, task_list):
        """Test unarchive workflow: unarchive task -> verify restored to normal view."""
        client = Client()
        client.force_login(user)

        # Create, complete, and archive a task
        task = Task.objects.create(
            title='Archived Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        task.mark_complete()
        task.archive()
        task.refresh_from_db()
        assert task.is_archived is True

        # Verify task is in archive view
        archive_url = reverse('tasks:archived-tasks')
        response = client.get(archive_url)
        assert response.status_code == 200
        archived_tasks = list(response.context['tasks'])
        assert task in archived_tasks

        # Unarchive the task
        unarchive_url = reverse('tasks:unarchive-task', kwargs={'pk': task.pk})
        response = client.post(unarchive_url)
        assert response.status_code == 200

        # Refresh task from database
        task.refresh_from_db()
        assert task.is_archived is False

        # Verify task is back in normal view
        list_url = reverse('tasks:task-list-all')
        response = client.get(list_url, {'status': 'all'})
        assert response.status_code == 200
        tasks = list(response.context['tasks'])
        assert task in tasks

        # Verify task is NOT in archive view anymore
        response = client.get(archive_url)
        assert response.status_code == 200
        archived_tasks = list(response.context['tasks'])
        assert task not in archived_tasks


@pytest.mark.django_db
class TestBulkArchiveWorkflow:
    """Test bulk archive workflow."""

    def test_bulk_archive_workflow_archives_all_completed_tasks(self, user, task_list):
        """Test bulk archive workflow: archive all completed -> verify all completed tasks archived."""
        client = Client()
        client.force_login(user)

        # Create mix of active and completed tasks
        active_tasks = []
        completed_tasks = []

        for i in range(3):
            task = Task.objects.create(
                title=f'Active Task {i+1}',
                priority='P2',
                task_list=task_list,
                created_by=user,
                status='active'
            )
            active_tasks.append(task)

        for i in range(4):
            task = Task.objects.create(
                title=f'Completed Task {i+1}',
                priority='P2',
                task_list=task_list,
                created_by=user,
                status='active'
            )
            task.mark_complete()
            completed_tasks.append(task)

        # Execute bulk archive all completed
        url = reverse('tasks:archive-all-completed', kwargs={'pk': task_list.pk})
        response = client.post(url)
        assert response.status_code == 200

        # Refresh all tasks from database
        for task in completed_tasks:
            task.refresh_from_db()
            assert task.is_archived is True

        for task in active_tasks:
            task.refresh_from_db()
            assert task.is_archived is False

        # Verify counts in normal view (only active tasks)
        list_url = reverse('tasks:task-list-all')
        response = client.get(list_url, {'status': 'all'})
        assert response.status_code == 200

        # Should only show 3 active tasks (4 completed tasks are archived)
        tasks = list(response.context['tasks'])
        assert len(tasks) == 3
        for active_task in active_tasks:
            assert active_task in tasks
        for completed_task in completed_tasks:
            assert completed_task not in tasks

        # Verify all completed tasks are in archive view
        archive_url = reverse('tasks:archived-tasks')
        response = client.get(archive_url)
        assert response.status_code == 200
        archived_tasks = list(response.context['tasks'])
        assert len(archived_tasks) == 4
        for completed_task in completed_tasks:
            assert completed_task in archived_tasks
