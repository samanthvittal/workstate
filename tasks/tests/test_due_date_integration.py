"""
Integration tests for due date management feature.
Tests end-to-end workflows and filter combinations.
"""
import pytest
from datetime import date, timedelta
from django.urls import reverse
from tasks.models import Task, Tag


@pytest.mark.django_db
class TestDueDateIntegration:
    """Integration tests for due date management workflows."""

    def test_filter_combination_today_view_with_workspace_and_tag(self, client, user, task_list, workspace):
        """Test that today view combines correctly with workspace and tag filters."""
        client.force_login(user)
        today = date.today()

        # Create tag
        tag = Tag.objects.create(
            name='urgent',
            workspace=workspace,
            created_by=user,
            color='#FF0000'
        )

        # Create tasks
        task_today_tagged = Task.objects.create(
            title='Task Today Tagged',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today,
            status='active'
        )
        task_today_tagged.tags.add(tag)

        task_today_untagged = Task.objects.create(
            title='Task Today Untagged',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today,
            status='active'
        )

        task_tomorrow_tagged = Task.objects.create(
            title='Task Tomorrow Tagged',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today + timedelta(days=1),
            status='active'
        )
        task_tomorrow_tagged.tags.add(tag)

        # Test combined filters: today + tag
        url = reverse('tasks:task-list-all') + f'?view=today&tag=urgent'
        response = client.get(url)

        tasks = response.context['tasks']
        assert task_today_tagged in tasks
        assert task_today_untagged not in tasks
        assert task_tomorrow_tagged not in tasks

    def test_quick_action_updates_task_and_changes_view_membership(self, client, user, task_list):
        """Test that quick actions update task due_date and affect view filtering."""
        client.force_login(user)
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # Create task with no due date
        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        # Initially task should appear in no_due_date view
        url = reverse('tasks:task-list-all') + '?view=no_due_date'
        response = client.get(url)
        assert task in response.context['tasks']

        # Use quick action to set due date to today
        quick_url = reverse('tasks:task-quick-date', kwargs={'pk': task.id})
        response = client.post(quick_url, {'action': 'today'}, HTTP_HX_REQUEST='true')
        assert response.status_code == 200

        # Reload task
        task.refresh_from_db()
        assert task.due_date == today

        # Now task should appear in today view
        url = reverse('tasks:task-list-all') + '?view=today'
        response = client.get(url)
        assert task in response.context['tasks']

        # And NOT in no_due_date view
        url = reverse('tasks:task-list-all') + '?view=no_due_date'
        response = client.get(url)
        assert task not in response.context['tasks']

    def test_navigation_badge_counts_update_based_on_filters(self, client, user, task_list, workspace):
        """Test that navigation badge counts reflect current filter state."""
        client.force_login(user)
        today = date.today()

        # Create tag
        tag = Tag.objects.create(
            name='work',
            workspace=workspace,
            created_by=user,
            color='#3B82F6'
        )

        # Create tasks
        task_today_work = Task.objects.create(
            title='Task Today Work',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today,
            status='active'
        )
        task_today_work.tags.add(tag)

        task_today_personal = Task.objects.create(
            title='Task Today Personal',
            priority='P2',
            task_list=task_list,
            created_by=user,
            due_date=today,
            status='active'
        )

        # Without tag filter, should see both tasks in count
        url = reverse('tasks:task-list-all')
        response = client.get(url)
        assert response.context['today_count'] == 2

        # With tag filter, should see only tagged task in count
        url = reverse('tasks:task-list-all') + '?tag=work'
        response = client.get(url)
        assert response.context['today_count'] == 1
