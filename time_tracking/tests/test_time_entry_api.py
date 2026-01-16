"""
Tests for time entry CRUD API endpoints.

Focused tests covering critical time entry operations:
- Create entry with three input modes
- Update entry
- Delete entry
- Validation rules
"""
import json
from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse

from accounts.models import Workspace
from tasks.models import Task, TaskList
from time_tracking.models import TimeEntry, UserTimePreferences


class TimeEntryCRUDAPITestCase(TestCase):
    """Test time entry CRUD API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()

        # Create user and authenticate
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        # Create workspace, task list, and task
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=self.user
        )
        self.task_list = TaskList.objects.create(
            name='Test Project',
            workspace=self.workspace,
            created_by=self.user
        )
        self.task = Task.objects.create(
            title='Test Task',
            task_list=self.task_list,
            created_by=self.user,
            priority='P3',  # Required field with valid value
        )

        # Create user preferences for time rounding
        self.preferences = UserTimePreferences.objects.create(
            user=self.user,
            rounding_interval=0,  # No rounding by default
            rounding_method='nearest'
        )

    def test_create_time_entry_mode_a_start_end_times(self):
        """Test creating time entry with Mode A: start_time + end_time."""
        start_time = timezone.now() - timedelta(hours=2)
        end_time = timezone.now()

        data = {
            'task_id': self.task.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'description': 'Test work',
        }

        response = self.client.post(
            '/api/time-entries/create/',
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        result = response.json()

        # Verify duration was calculated automatically
        self.assertIn('duration', result)
        self.assertGreater(result['duration'], 0)

        # Verify project inherited from task
        self.assertEqual(result['project']['id'], self.task_list.id)

        # Verify entry was saved to database
        entry = TimeEntry.objects.get(id=result['id'])
        self.assertEqual(entry.task_id, self.task.id)
        self.assertEqual(entry.project_id, self.task_list.id)
        self.assertIsNotNone(entry.start_time)
        self.assertIsNotNone(entry.end_time)

    def test_create_time_entry_mode_b_start_duration(self):
        """Test creating time entry with Mode B: start_time + duration."""
        start_time = timezone.now() - timedelta(hours=1)
        duration_seconds = 3600  # 1 hour

        data = {
            'task_id': self.task.id,
            'start_time': start_time.isoformat(),
            'duration': duration_seconds,
            'description': 'Test work mode B',
        }

        response = self.client.post(
            '/api/time-entries/create/',
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        result = response.json()

        # Verify end_time was calculated automatically
        self.assertIn('end_time', result)
        self.assertIsNotNone(result['end_time'])

        # Verify duration matches input
        self.assertEqual(result['duration'], duration_seconds)

    def test_create_time_entry_mode_c_duration_only(self):
        """Test creating time entry with Mode C: duration only."""
        duration_seconds = 7200  # 2 hours

        data = {
            'task_id': self.task.id,
            'duration': duration_seconds,
            'description': 'Test work mode C',
            'is_billable': True,
            'billable_rate': '75.00',
        }

        response = self.client.post(
            '/api/time-entries/create/',
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        result = response.json()

        # Verify start_time and end_time are null
        self.assertIsNone(result['start_time'])
        self.assertIsNone(result['end_time'])

        # Verify duration is set
        self.assertEqual(result['duration'], duration_seconds)

        # Verify billable fields
        self.assertTrue(result['is_billable'])
        self.assertEqual(result['billable_rate'], '75.00')

    def test_create_time_entry_validation_end_before_start(self):
        """Test validation: end_time must be after start_time."""
        start_time = timezone.now()
        end_time = start_time - timedelta(hours=1)  # Invalid: end before start

        data = {
            'task_id': self.task.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
        }

        response = self.client.post(
            '/api/time-entries/create/',
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_update_time_entry(self):
        """Test updating an existing time entry."""
        # Create a time entry first
        entry = TimeEntry.objects.create(
            user=self.user,
            task=self.task,
            project=self.task_list,
            duration=timedelta(hours=1),
            description='Original description',
            is_running=False,
        )

        # Update the entry
        new_duration_seconds = 7200  # 2 hours
        data = {
            'duration': new_duration_seconds,
            'description': 'Updated description',
            'is_billable': True,
        }

        response = self.client.patch(
            f'/api/time-entries/{entry.id}/update/',
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()

        # Verify updates
        self.assertEqual(result['duration'], new_duration_seconds)
        self.assertEqual(result['description'], 'Updated description')
        self.assertTrue(result['is_billable'])

        # Verify in database
        entry.refresh_from_db()
        self.assertEqual(entry.duration, timedelta(seconds=new_duration_seconds))
        self.assertEqual(entry.description, 'Updated description')

    def test_update_prevents_editing_running_timer(self):
        """Test that running timers cannot be edited via CRUD API."""
        # Create a running timer
        entry = TimeEntry.objects.create(
            user=self.user,
            task=self.task,
            project=self.task_list,
            start_time=timezone.now(),
            duration=timedelta(0),
            is_running=True,
        )

        data = {
            'description': 'Trying to update running timer',
        }

        response = self.client.patch(
            f'/api/time-entries/{entry.id}/update/',
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_delete_time_entry(self):
        """Test deleting a time entry."""
        # Create a time entry
        entry = TimeEntry.objects.create(
            user=self.user,
            task=self.task,
            project=self.task_list,
            duration=timedelta(hours=1),
            is_running=False,
        )

        response = self.client.delete(f'/api/time-entries/{entry.id}/delete/')

        self.assertEqual(response.status_code, 204)

        # Verify entry was deleted
        self.assertFalse(TimeEntry.objects.filter(id=entry.id).exists())

    def test_delete_prevents_deleting_running_timer(self):
        """Test that running timers cannot be deleted via CRUD API."""
        # Create a running timer
        entry = TimeEntry.objects.create(
            user=self.user,
            task=self.task,
            project=self.task_list,
            start_time=timezone.now(),
            duration=timedelta(0),
            is_running=True,
        )

        response = self.client.delete(f'/api/time-entries/{entry.id}/delete/')

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

        # Verify entry still exists
        self.assertTrue(TimeEntry.objects.filter(id=entry.id).exists())
