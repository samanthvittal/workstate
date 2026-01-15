"""
Tests for Task Status & Completion feature (T008) - Task Groups 1, 2 & 3.

This test file covers:
- Task Group 1: Database schema enhancements (model fields, methods, constraints)
- Task Group 2: Status toggle and filtering views
- Task Group 3: Bulk complete and archive functionality
"""
import pytest
from datetime import date, timedelta
from django.utils import timezone
from django.db import IntegrityError
from django.test import Client
from django.urls import reverse
from tasks.models import Task
from accounts.models import UserPreference


@pytest.mark.django_db
class TestTaskCompletionTimestamps:
    """Test suite for completed_at timestamp management."""

    def test_completed_at_is_set_when_marking_task_complete(self, user, task_list):
        """Test that completed_at is set to current time when marking task complete."""
        # Create an active task
        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        # Ensure completed_at is initially None
        assert task.completed_at is None
        assert task.status == 'active'

        # Mark task as complete
        task.mark_complete()
        task.refresh_from_db()

        # Verify completed_at is now set
        assert task.completed_at is not None
        assert task.status == 'completed'

        # Verify completed_at is recent (within last minute)
        time_diff = timezone.now() - task.completed_at
        assert time_diff.total_seconds() < 60

    def test_completed_at_is_cleared_when_marking_task_active(self, user, task_list):
        """Test that completed_at is cleared when marking task active again."""
        # Create a completed task
        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        # Mark complete first
        task.mark_complete()
        task.refresh_from_db()
        assert task.completed_at is not None
        assert task.status == 'completed'

        # Mark active again
        task.mark_active()
        task.refresh_from_db()

        # Verify completed_at is now None
        assert task.completed_at is None
        assert task.status == 'active'


@pytest.mark.django_db
class TestTaskArchival:
    """Test suite for task archival functionality."""

    def test_is_archived_excludes_task_from_active_queries(self, user, task_list):
        """Test that is_archived=True excludes task from active queries."""
        # Create two tasks
        active_task = Task.objects.create(
            title='Active Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        archived_task = Task.objects.create(
            title='Archived Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='completed'
        )

        # Archive the second task
        archived_task.archive()
        archived_task.refresh_from_db()

        # Verify is_archived is set
        assert archived_task.is_archived is True
        assert active_task.is_archived is False

        # Query for non-archived tasks
        non_archived_tasks = Task.objects.filter(
            task_list=task_list,
            is_archived=False
        )

        # Verify only active task is returned
        assert active_task in non_archived_tasks
        assert archived_task not in non_archived_tasks
        assert non_archived_tasks.count() == 1

    def test_unarchive_restores_archived_task(self, user, task_list):
        """Test that unarchive() method restores archived task."""
        # Create and archive a task
        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='completed'
        )

        task.archive()
        task.refresh_from_db()
        assert task.is_archived is True

        # Unarchive the task
        task.unarchive()
        task.refresh_from_db()

        # Verify is_archived is now False
        assert task.is_archived is False


@pytest.mark.django_db
class TestCompletedAtConstraint:
    """Test suite for database constraint on completed_at field."""

    def test_database_constraint_ensures_completed_at_only_set_when_status_completed(self, user, task_list):
        """Test that completed_at can only be set when status='completed'."""
        # Create an active task
        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        # Attempt to set completed_at while status is active should fail via constraint
        # Note: This tests the database constraint, so we use update() to bypass model validation
        with pytest.raises(IntegrityError):
            Task.objects.filter(pk=task.pk).update(
                completed_at=timezone.now(),
                status='active'
            )


@pytest.mark.django_db
class TestTaskToggleStatusView:
    """Test suite for TaskToggleStatusView (Task Group 2)."""

    def test_task_toggle_status_flips_task_status_correctly(self, user, task_list):
        """Test that TaskToggleStatusView flips task status from active to completed."""
        # Create an active task
        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        # Login and send POST request
        client = Client()
        client.force_login(user)
        url = reverse('tasks:toggle-status', kwargs={'pk': task.pk})
        response = client.post(url)

        # Verify response is successful
        assert response.status_code == 200

        # Refresh task from database
        task.refresh_from_db()

        # Verify task is now completed
        assert task.status == 'completed'
        assert task.completed_at is not None

    def test_task_toggle_status_updates_completed_at_timestamp(self, user, task_list):
        """Test that TaskToggleStatusView updates completed_at timestamp when toggling to completed."""
        # Create a completed task
        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        task.mark_complete()
        task.refresh_from_db()

        assert task.status == 'completed'
        assert task.completed_at is not None
        initial_completed_at = task.completed_at

        # Toggle back to active
        client = Client()
        client.force_login(user)
        url = reverse('tasks:toggle-status', kwargs={'pk': task.pk})
        response = client.post(url)

        # Verify response is successful
        assert response.status_code == 200

        # Refresh task from database
        task.refresh_from_db()

        # Verify task is now active and completed_at is cleared
        assert task.status == 'active'
        assert task.completed_at is None


@pytest.mark.django_db
class TestStatusFilteringLogic:
    """Test suite for status filtering in TaskListView (Task Group 2)."""

    def test_status_filter_query_parameter_filters_tasks_correctly(self, user, task_list):
        """Test that status filter query parameter filters tasks correctly."""
        # Create multiple tasks with different statuses
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

        # Login and request with status=active filter
        client = Client()
        client.force_login(user)
        url = reverse('tasks:task-list-all')
        response = client.get(url, {'status': 'active'})

        # Verify response is successful
        assert response.status_code == 200

        # Verify only active task is in response
        tasks = response.context['tasks']
        assert active_task in tasks
        assert completed_task not in tasks

        # Test completed filter
        response = client.get(url, {'status': 'completed'})
        assert response.status_code == 200
        tasks = response.context['tasks']
        assert active_task not in tasks
        assert completed_task in tasks

        # Test all filter
        response = client.get(url, {'status': 'all'})
        assert response.status_code == 200
        tasks = response.context['tasks']
        assert active_task in tasks
        assert completed_task in tasks

    def test_status_filter_persists_to_user_preferences(self, user, task_list):
        """Test that status filter persists to UserPreferences."""
        # Create user preferences if not exists
        user_prefs, created = UserPreference.objects.get_or_create(user=user)
        assert user_prefs.default_task_status_filter == 'active'

        # Login and change filter to completed
        client = Client()
        client.force_login(user)
        url = reverse('tasks:task-list-all')
        response = client.get(url, {'status': 'completed'})

        # Verify response is successful
        assert response.status_code == 200

        # Refresh user preferences from database
        user_prefs.refresh_from_db()

        # Verify preference was updated
        assert user_prefs.default_task_status_filter == 'completed'


@pytest.mark.django_db
class TestBulkCompleteActions:
    """Test suite for bulk complete actions (Task Group 3)."""

    def test_mark_all_complete_marks_all_active_tasks_in_list(self, user, task_list):
        """Test that TaskListMarkAllCompleteView marks all active tasks as complete."""
        # Create multiple active tasks
        task1 = Task.objects.create(
            title='Task 1',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        task2 = Task.objects.create(
            title='Task 2',
            priority='P3',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        task3 = Task.objects.create(
            title='Task 3',
            priority='P1',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        # Create a completed task (should remain unchanged)
        completed_task = Task.objects.create(
            title='Already Completed',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        completed_task.mark_complete()

        # Login and send POST request
        client = Client()
        client.force_login(user)
        url = reverse('tasks:mark-all-complete', kwargs={'pk': task_list.pk})
        response = client.post(url)

        # Verify response is successful
        assert response.status_code == 200

        # Refresh tasks from database
        task1.refresh_from_db()
        task2.refresh_from_db()
        task3.refresh_from_db()
        completed_task.refresh_from_db()

        # Verify all active tasks are now completed
        assert task1.status == 'completed'
        assert task1.completed_at is not None
        assert task2.status == 'completed'
        assert task2.completed_at is not None
        assert task3.status == 'completed'
        assert task3.completed_at is not None

        # Verify already completed task remains unchanged
        assert completed_task.status == 'completed'

    def test_task_archive_view_archives_single_task(self, user, task_list):
        """Test TaskArchiveView archives single task correctly."""
        # Create a completed task
        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        task.mark_complete()

        # Login and send POST request
        client = Client()
        client.force_login(user)
        url = reverse('tasks:archive-task', kwargs={'pk': task.pk})
        response = client.post(url)

        # Verify response is successful
        assert response.status_code == 200

        # Refresh task from database
        task.refresh_from_db()

        # Verify task is archived
        assert task.is_archived is True
        assert task.status == 'completed'

    def test_archive_all_completed_archives_all_completed_tasks_in_list(self, user, task_list):
        """Test TaskListArchiveAllCompletedView archives all completed tasks."""
        # Create multiple completed tasks
        task1 = Task.objects.create(
            title='Completed Task 1',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        task1.mark_complete()

        task2 = Task.objects.create(
            title='Completed Task 2',
            priority='P3',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        task2.mark_complete()

        # Create an active task (should remain unchanged)
        active_task = Task.objects.create(
            title='Active Task',
            priority='P1',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        # Login and send POST request
        client = Client()
        client.force_login(user)
        url = reverse('tasks:archive-all-completed', kwargs={'pk': task_list.pk})
        response = client.post(url)

        # Verify response is successful
        assert response.status_code == 200

        # Refresh tasks from database
        task1.refresh_from_db()
        task2.refresh_from_db()
        active_task.refresh_from_db()

        # Verify completed tasks are archived
        assert task1.is_archived is True
        assert task2.is_archived is True

        # Verify active task remains unchanged
        assert active_task.is_archived is False

    def test_archived_task_list_view_shows_only_archived_tasks(self, user, task_list):
        """Test ArchivedTaskListView displays only archived tasks."""
        # Create archived tasks
        archived_task1 = Task.objects.create(
            title='Archived Task 1',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        archived_task1.mark_complete()
        archived_task1.archive()

        archived_task2 = Task.objects.create(
            title='Archived Task 2',
            priority='P3',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        archived_task2.mark_complete()
        archived_task2.archive()

        # Create non-archived tasks
        active_task = Task.objects.create(
            title='Active Task',
            priority='P1',
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

        # Login and send GET request
        client = Client()
        client.force_login(user)
        url = reverse('tasks:archived-tasks')
        response = client.get(url)

        # Verify response is successful
        assert response.status_code == 200

        # Verify only archived tasks are in response
        tasks = response.context['tasks']
        assert archived_task1 in tasks
        assert archived_task2 in tasks
        assert active_task not in tasks
        assert completed_task not in tasks
        assert tasks.count() == 2
