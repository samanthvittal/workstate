"""
Tests for timer widget UI component.

Focused tests covering critical timer widget behaviors: rendering active timer,
live countdown updates, and stop/discard button actions.
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.models import Workspace
from tasks.models import Task, TaskList
from time_tracking.models import TimeEntry
from time_tracking.services.cache import TimeEntryCache


class TimerWidgetTestCase(TestCase):
    """Test suite for timer widget component."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create workspace and task list
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=self.user
        )
        self.task_list = TaskList.objects.create(
            name='Test Project',
            workspace=self.workspace,
            created_by=self.user
        )

        # Create test task
        self.task = Task.objects.create(
            title='Test Task',
            task_list=self.task_list,
            created_by=self.user,
            priority='P3'
        )

        # Create client and login
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def tearDown(self):
        """Clean up after each test."""
        TimeEntryCache.clear_active_timer(self.user.id)

    def test_widget_renders_when_timer_active(self):
        """Test widget displays active timer data correctly."""
        # Start a timer
        response = self.client.post(
            '/api/timers/start/',
            data=json.dumps({
                'task_id': self.task.id,
                'description': 'Working on feature'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        # Get active timer via API (simulates widget initialization)
        response = self.client.get('/api/timers/active/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['is_running'])
        # Cache returns flat structure, serializer returns nested
        task_title = data.get('task_title') or data.get('task', {}).get('title')
        self.assertEqual(task_title, 'Test Task')
        self.assertEqual(data['description'], 'Working on feature')
        self.assertIn('elapsed_time', data)

    def test_widget_hidden_when_no_active_timer(self):
        """Test widget returns 404 when no active timer exists."""
        response = self.client.get('/api/timers/active/')
        self.assertEqual(response.status_code, 404)

    def test_stop_button_stops_timer(self):
        """Test clicking stop button stops the timer."""
        # Start timer
        start_response = self.client.post(
            '/api/timers/start/',
            data=json.dumps({'task_id': self.task.id}),
            content_type='application/json'
        )
        self.assertEqual(start_response.status_code, 201)
        timer_id = start_response.json()['id']

        # Stop timer (simulates stop button click)
        stop_response = self.client.post(
            '/api/timers/stop/',
            content_type='application/json'
        )
        self.assertEqual(stop_response.status_code, 200)

        # Verify timer is stopped
        timer = TimeEntry.objects.get(id=timer_id)
        self.assertFalse(timer.is_running)
        self.assertIsNotNone(timer.end_time)

    def test_discard_button_deletes_timer(self):
        """Test clicking discard button with confirmation deletes timer."""
        # Start timer
        start_response = self.client.post(
            '/api/timers/start/',
            data=json.dumps({'task_id': self.task.id}),
            content_type='application/json'
        )
        self.assertEqual(start_response.status_code, 201)
        timer_id = start_response.json()['id']

        # Discard timer with confirmation (simulates discard button click)
        discard_response = self.client.post(
            '/api/timers/discard/',
            data=json.dumps({'confirmed': True}),
            content_type='application/json'
        )
        self.assertEqual(discard_response.status_code, 200)

        # Verify timer is deleted
        self.assertFalse(TimeEntry.objects.filter(id=timer_id).exists())

    def test_timer_countdown_updates_elapsed_time(self):
        """Test elapsed time increases as timer runs."""
        # Start timer
        start_response = self.client.post(
            '/api/timers/start/',
            data=json.dumps({'task_id': self.task.id}),
            content_type='application/json'
        )
        self.assertEqual(start_response.status_code, 201)

        # Get active timer immediately
        response1 = self.client.get('/api/timers/active/')
        elapsed_time_1 = response1.json()['elapsed_time']

        # Wait a moment and get again
        import time
        time.sleep(1)

        response2 = self.client.get('/api/timers/active/')
        elapsed_time_2 = response2.json()['elapsed_time']

        # Elapsed time should have increased
        self.assertGreater(elapsed_time_2, elapsed_time_1)

    def test_discard_confirmation_dialog_data(self):
        """Test discard without confirmation returns dialog data."""
        # Start timer
        start_response = self.client.post(
            '/api/timers/start/',
            data=json.dumps({'task_id': self.task.id}),
            content_type='application/json'
        )
        self.assertEqual(start_response.status_code, 201)

        # Request discard without confirmation
        discard_response = self.client.post(
            '/api/timers/discard/',
            data=json.dumps({'confirmed': False}),
            content_type='application/json'
        )

        self.assertEqual(discard_response.status_code, 200)
        data = discard_response.json()

        # Verify confirmation dialog structure
        self.assertTrue(data.get('confirmation_required'))
        self.assertIn('timer', data)
        self.assertIn('elapsed_time', data['timer'])
        self.assertIn('message', data)
