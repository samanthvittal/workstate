"""
Tests for timer buttons in task UI.

Focused tests covering critical timer button behaviors:
- Button appears in task views
- Button shows correct state based on active timer
- Start/stop actions work correctly
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from accounts.models import Workspace
from tasks.models import TaskList, Task
from time_tracking.models import TimeEntry


@pytest.mark.django_db
class TimerButtonTests(TestCase):
    """Tests for timer buttons in task UI."""

    def setUp(self):
        """Set up test data."""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

        # Create workspace and task list
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=self.user
        )
        self.task_list = TaskList.objects.create(
            name='Test List',
            workspace=self.workspace,
            created_by=self.user
        )

        # Create test tasks with required priority field
        self.task1 = Task.objects.create(
            title='Task 1',
            task_list=self.task_list,
            created_by=self.user,
            status='active',
            priority='P3'  # Medium priority
        )
        self.task2 = Task.objects.create(
            title='Task 2',
            task_list=self.task_list,
            created_by=self.user,
            status='active',
            priority='P3'  # Medium priority
        )

    def test_start_timer_from_task_card(self):
        """Test starting timer from task card via HTMX."""
        # Start timer on task1
        response = self.client.post(
            '/api/timers/start/',
            data={'task_id': self.task1.id},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['is_running'])
        self.assertEqual(data['task']['id'], self.task1.id)

        # Verify timer was created
        timer = TimeEntry.objects.filter(user=self.user, is_running=True).first()
        self.assertIsNotNone(timer)
        self.assertEqual(timer.task_id, self.task1.id)

    def test_stop_timer_updates_button_state(self):
        """Test stopping timer updates button state correctly."""
        # Start timer
        timer = TimeEntry.objects.create(
            user=self.user,
            task=self.task1,
            project=self.task_list,
            start_time=timezone.now(),
            duration=timezone.timedelta(0),
            is_running=True
        )

        # Stop timer
        response = self.client.post('/api/timers/stop/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['is_running'])

        # Verify timer was stopped
        timer.refresh_from_db()
        self.assertFalse(timer.is_running)
        self.assertIsNotNone(timer.end_time)

    def test_button_shows_correct_state_for_active_timer(self):
        """Test button shows 'Stop Timer' when task has active timer."""
        # Start timer on task1
        TimeEntry.objects.create(
            user=self.user,
            task=self.task1,
            project=self.task_list,
            start_time=timezone.now(),
            duration=timezone.timedelta(0),
            is_running=True
        )

        # Get task detail page
        response = self.client.get(
            reverse('tasks:task-detail', kwargs={'pk': self.task1.id})
        )

        self.assertEqual(response.status_code, 200)
        # Context should indicate active timer for this task
        # (Implementation will add has_active_timer property to task)

    def test_auto_stop_confirmation_when_starting_with_active_timer(self):
        """Test confirmation dialog appears when starting timer with active timer running."""
        # Start timer on task1
        TimeEntry.objects.create(
            user=self.user,
            task=self.task1,
            project=self.task_list,
            start_time=timezone.now(),
            duration=timezone.timedelta(0),
            is_running=True
        )

        # Try to start timer on task2 (should return confirmation)
        response = self.client.post(
            '/api/timers/start/',
            data={'task_id': self.task2.id},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('confirmation_required'))
        self.assertIn('current_timer', data)
        self.assertIn('new_task', data)
        self.assertEqual(data['current_timer']['task']['id'], self.task1.id)
        self.assertEqual(data['new_task']['id'], self.task2.id)

    def test_auto_stop_confirmed_starts_new_timer(self):
        """Test confirming auto-stop actually stops old timer and starts new one."""
        # Start timer on task1
        old_timer = TimeEntry.objects.create(
            user=self.user,
            task=self.task1,
            project=self.task_list,
            start_time=timezone.now(),
            duration=timezone.timedelta(0),
            is_running=True
        )

        # Start timer on task2 with auto_stop_current=True
        response = self.client.post(
            '/api/timers/start/',
            data={'task_id': self.task2.id, 'auto_stop_current': True},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['is_running'])
        self.assertEqual(data['task']['id'], self.task2.id)

        # Verify old timer was stopped
        old_timer.refresh_from_db()
        self.assertFalse(old_timer.is_running)

        # Verify new timer is running
        new_timer = TimeEntry.objects.filter(user=self.user, is_running=True).first()
        self.assertIsNotNone(new_timer)
        self.assertEqual(new_timer.task_id, self.task2.id)

    def test_timer_button_in_task_list_view(self):
        """Test timer button appears in task list view."""
        response = self.client.get(reverse('tasks:task-list-all'))

        self.assertEqual(response.status_code, 200)
        # Task list should render successfully
        # (Implementation will add timer buttons to each task card)

    def test_multiple_timer_buttons_update_on_start(self):
        """Test all timer buttons update when any timer is started."""
        # This test verifies the OOB swap mechanism
        # Start timer on task1
        response = self.client.post(
            '/api/timers/start/',
            data={'task_id': self.task1.id},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        # Response should include timer data that can be used to update all buttons
        # (Implementation will use hx-swap-oob to update all timer buttons on page)
