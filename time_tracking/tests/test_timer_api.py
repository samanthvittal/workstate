"""
Tests for timer API endpoints.

Focused tests covering critical timer operations: start, stop, discard,
and single active timer enforcement.
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from accounts.models import Workspace
from tasks.models import Task, TaskList
from time_tracking.models import TimeEntry, UserTimePreferences
from time_tracking.services.cache import TimeEntryCache


class TimerAPITestCase(TestCase):
    """Test suite for timer API endpoints."""

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

        # Create test task with required priority field
        self.task = Task.objects.create(
            title='Test Task',
            task_list=self.task_list,
            created_by=self.user,
            priority='P3'  # Required field
        )

        # Create another task for testing
        self.task2 = Task.objects.create(
            title='Test Task 2',
            task_list=self.task_list,
            created_by=self.user,
            priority='P3'
        )

        # Create client and login
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

        # Create user preferences with rounding
        UserTimePreferences.objects.create(
            user=self.user,
            rounding_interval=5,
            rounding_method='nearest'
        )

    def tearDown(self):
        """Clean up after each test."""
        # Clear any cached timers
        TimeEntryCache.clear_active_timer(self.user.id)

    def test_start_timer_creates_new_timer(self):
        """Test starting a timer creates a new TimeEntry."""
        response = self.client.post(
            '/api/timers/start/',
            data=json.dumps({
                'task_id': self.task.id,
                'description': 'Working on feature'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()

        # Verify response structure
        self.assertIn('id', data)
        self.assertEqual(data['task']['id'], self.task.id)
        self.assertEqual(data['description'], 'Working on feature')
        self.assertTrue(data['is_running'])

        # Verify database record
        timer = TimeEntry.objects.get(id=data['id'])
        self.assertEqual(timer.user, self.user)
        self.assertEqual(timer.task, self.task)
        self.assertTrue(timer.is_running)

    def test_start_timer_without_task_id_fails(self):
        """Test starting timer without task_id returns error."""
        response = self.client.post(
            '/api/timers/start/',
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Task ID', data['error'])

    def test_single_active_timer_enforcement(self):
        """Test only one timer can be active at a time."""
        # Start first timer
        response1 = self.client.post(
            '/api/timers/start/',
            data=json.dumps({'task_id': self.task.id}),
            content_type='application/json'
        )
        self.assertEqual(response1.status_code, 201)

        # Try to start second timer without confirmation
        response2 = self.client.post(
            '/api/timers/start/',
            data=json.dumps({'task_id': self.task2.id}),
            content_type='application/json'
        )

        # Should return confirmation dialog
        self.assertEqual(response2.status_code, 200)
        data = response2.json()
        self.assertTrue(data.get('confirmation_required'))
        self.assertIn('current_timer', data)

    def test_auto_stop_previous_timer(self):
        """Test starting new timer with auto_stop_current stops previous timer."""
        # Start first timer
        response1 = self.client.post(
            '/api/timers/start/',
            data=json.dumps({'task_id': self.task.id}),
            content_type='application/json'
        )
        timer1_id = response1.json()['id']

        # Start second timer with auto_stop_current=True
        response2 = self.client.post(
            '/api/timers/start/',
            data=json.dumps({
                'task_id': self.task2.id,
                'auto_stop_current': True
            }),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, 201)

        # Verify first timer is stopped
        timer1 = TimeEntry.objects.get(id=timer1_id)
        self.assertFalse(timer1.is_running)
        self.assertIsNotNone(timer1.end_time)

        # Verify second timer is running
        timer2_id = response2.json()['id']
        timer2 = TimeEntry.objects.get(id=timer2_id)
        self.assertTrue(timer2.is_running)

    def test_stop_timer_calculates_duration(self):
        """Test stopping timer calculates duration correctly."""
        # Start timer
        response1 = self.client.post(
            '/api/timers/start/',
            data=json.dumps({'task_id': self.task.id}),
            content_type='application/json'
        )
        timer_id = response1.json()['id']

        # Stop timer
        response2 = self.client.post(
            '/api/timers/stop/',
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, 200)
        data = response2.json()

        # Verify timer is stopped
        self.assertFalse(data['is_running'])
        self.assertIsNotNone(data['end_time'])
        self.assertGreater(data['duration'], 0)

        # Verify database
        timer = TimeEntry.objects.get(id=timer_id)
        self.assertFalse(timer.is_running)
        self.assertGreater(timer.duration.total_seconds(), 0)

    def test_discard_timer_deletes_record(self):
        """Test discarding timer with confirmation deletes the record."""
        # Start timer
        response1 = self.client.post(
            '/api/timers/start/',
            data=json.dumps({'task_id': self.task.id}),
            content_type='application/json'
        )
        timer_id = response1.json()['id']

        # Discard timer with confirmation via POST
        response2 = self.client.post(
            '/api/timers/discard/',
            data=json.dumps({'confirmed': True}),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, 200)
        data = response2.json()
        self.assertIn('message', data)

        # Verify timer is deleted
        self.assertFalse(
            TimeEntry.objects.filter(id=timer_id).exists()
        )

    def test_get_active_timer_returns_running_timer(self):
        """Test getting active timer returns correct data."""
        # Start timer
        response1 = self.client.post(
            '/api/timers/start/',
            data=json.dumps({
                'task_id': self.task.id,
                'description': 'Test work'
            }),
            content_type='application/json'
        )
        timer_id = response1.json()['id']

        # Get active timer
        response2 = self.client.get('/api/timers/active/')

        self.assertEqual(response2.status_code, 200)
        data = response2.json()

        # Verify returned data
        self.assertEqual(data['id'], timer_id)
        self.assertTrue(data['is_running'])
        self.assertEqual(data['task_id'], self.task.id)
        self.assertIn('elapsed_time', data)

    def test_get_active_timer_without_running_timer(self):
        """Test getting active timer when none exists returns 404."""
        response = self.client.get('/api/timers/active/')

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)
