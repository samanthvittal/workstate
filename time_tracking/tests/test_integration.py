"""
Integration tests for time tracking feature.

These tests verify critical end-to-end workflows across multiple components:
timer API + cache + database, manual entry creation through all three modes,
filtering workflows, and cross-component integration.

Maximum 10 strategic tests focusing on integration points.
"""
import json
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse

from accounts.models import Workspace
from tasks.models import Task, TaskList, Tag
from time_tracking.models import TimeEntry, UserTimePreferences
from time_tracking.services.cache import TimeEntryCache


class TimerLifecycleIntegrationTest(TestCase):
    """Test complete timer lifecycle: start -> edit -> stop -> view in list."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
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
            title='Integration Test Task',
            task_list=self.task_list,
            created_by=self.user,
            priority='P2'
        )

        # Create time preferences with rounding
        UserTimePreferences.objects.create(
            user=self.user,
            rounding_interval=15,
            rounding_method='nearest'
        )

    def test_complete_timer_lifecycle(self):
        """Test start timer -> edit description -> stop -> verify in list."""
        # Step 1: Start timer
        response = self.client.post(
            reverse('time_tracking:timer-start'),
            data=json.dumps({'task_id': self.task.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['is_running'])
        timer_id = data['id']

        # Verify timer in database
        timer = TimeEntry.objects.get(id=timer_id)
        self.assertTrue(timer.is_running)
        self.assertEqual(timer.task_id, self.task.id)

        # Verify timer in cache
        cache_service = TimeEntryCache()
        cached_timer = cache_service.get_active_timer(self.user.id)
        self.assertIsNotNone(cached_timer)

        # Step 2: Edit description (simulate quick edit in widget)
        timer.description = "Working on integration test"
        timer.save()

        # Step 3: Stop timer (after simulated elapsed time)
        response = self.client.post(
            reverse('time_tracking:timer-stop'),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['is_running'])
        self.assertIsNotNone(data['end_time'])
        self.assertGreater(data['duration'], 0)

        # Verify timer stopped in database
        timer.refresh_from_db()
        self.assertFalse(timer.is_running)
        self.assertIsNotNone(timer.end_time)
        self.assertEqual(timer.description, "Working on integration test")

        # Verify timer removed from cache
        cached_timer = cache_service.get_active_timer(self.user.id)
        self.assertIsNone(cached_timer)

        # Step 4: Verify timer appears in time entries list
        response = self.client.get(reverse('time_tracking:time-entry-list-html'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Integration Test Task')
        self.assertContains(response, 'Working on integration test')


class ManualEntryThreeModesIntegrationTest(TestCase):
    """Test manual entry creation with all three input modes."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=self.user
        )
        task_list = TaskList.objects.create(
            name='Test Project',
            workspace=workspace,
            created_by=self.user
        )
        self.task = Task.objects.create(
            title='Manual Entry Task',
            task_list=task_list,
            created_by=self.user,
            priority='P3'
        )

    def test_mode_a_start_and_end_time(self):
        """Test Mode A: start_time + end_time provided (calculates duration)."""
        start_time = timezone.now() - timedelta(hours=2)
        end_time = timezone.now()

        response = self.client.post(
            reverse('time_tracking:time-entry-create'),
            data=json.dumps({
                'task_id': self.task.id,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'description': 'Mode A test'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()

        # Verify duration was calculated
        self.assertIsNotNone(data['duration'])
        entry = TimeEntry.objects.get(id=data['id'])
        expected_duration = end_time - start_time
        self.assertAlmostEqual(
            entry.duration.total_seconds(),
            expected_duration.total_seconds(),
            delta=60
        )

    def test_mode_b_start_time_and_duration(self):
        """Test Mode B: start_time + duration provided (calculates end_time)."""
        start_time = timezone.now() - timedelta(hours=1)
        duration_seconds = 3600  # 1 hour

        response = self.client.post(
            reverse('time_tracking:time-entry-create'),
            data=json.dumps({
                'task_id': self.task.id,
                'start_time': start_time.isoformat(),
                'duration': duration_seconds,
                'description': 'Mode B test'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()

        # Verify end_time was calculated
        self.assertIsNotNone(data['end_time'])
        entry = TimeEntry.objects.get(id=data['id'])
        expected_end_time = start_time + timedelta(seconds=duration_seconds)
        self.assertAlmostEqual(
            entry.end_time.timestamp(),
            expected_end_time.timestamp(),
            delta=60
        )

    def test_mode_c_duration_only(self):
        """Test Mode C: duration only (no start/end times)."""
        duration_seconds = 7200  # 2 hours

        response = self.client.post(
            reverse('time_tracking:time-entry-create'),
            data=json.dumps({
                'task_id': self.task.id,
                'duration': duration_seconds,
                'description': 'Mode C test'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()

        # Verify no start/end times set
        entry = TimeEntry.objects.get(id=data['id'])
        self.assertIsNone(entry.start_time)
        self.assertIsNone(entry.end_time)
        self.assertEqual(entry.duration.total_seconds(), duration_seconds)


class FilterWorkflowIntegrationTest(TestCase):
    """Test applying multiple filters and verifying results."""

    def setUp(self):
        """Set up test fixtures with multiple entries."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=self.user
        )
        task_list = TaskList.objects.create(
            name='Project A',
            workspace=workspace,
            created_by=self.user
        )

        # Create multiple tasks and time entries
        self.task1 = Task.objects.create(
            title='Task 1',
            task_list=task_list,
            created_by=self.user,
            priority='P1'
        )
        self.task2 = Task.objects.create(
            title='Task 2',
            task_list=task_list,
            created_by=self.user,
            priority='P2'
        )

        # Create time entries with varying properties
        now = timezone.now()
        TimeEntry.objects.create(
            user=self.user,
            task=self.task1,
            start_time=now - timedelta(days=2),
            duration=timedelta(hours=2),
            is_billable=True,
            billable_rate=100.0
        )
        TimeEntry.objects.create(
            user=self.user,
            task=self.task2,
            start_time=now - timedelta(days=1),
            duration=timedelta(hours=3),
            is_billable=False
        )
        TimeEntry.objects.create(
            user=self.user,
            task=self.task1,
            start_time=now,
            duration=timedelta(hours=1),
            is_billable=True,
            billable_rate=100.0
        )

    def test_filter_by_date_range(self):
        """Test filtering by custom date range."""
        start_date = (timezone.now() - timedelta(days=1)).date()
        end_date = timezone.now().date()

        response = self.client.get(
            reverse('time_tracking:time-entry-list-html'),
            {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()}
        )
        self.assertEqual(response.status_code, 200)
        # Should show 2 entries within range
        self.assertContains(response, 'Task 1')
        self.assertContains(response, 'Task 2')

    def test_filter_by_task_and_billable(self):
        """Test filtering by task and billable status."""
        response = self.client.get(
            reverse('time_tracking:time-entry-list-html'),
            {'task_id': self.task1.id, 'billable': 'billable'}
        )
        self.assertEqual(response.status_code, 200)
        # Should show only billable entries for task1
        content = response.content.decode()
        self.assertIn('Task 1', content)


class CrossComponentIntegrationTest(TestCase):
    """Test integration between timer, cache, and database."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=self.user
        )
        task_list = TaskList.objects.create(
            name='Test Project',
            workspace=workspace,
            created_by=self.user
        )
        self.task = Task.objects.create(
            title='Cache Sync Task',
            task_list=task_list,
            created_by=self.user,
            priority='P1'
        )

    def test_timer_cache_database_consistency(self):
        """Test that timer state stays consistent across cache and database."""
        cache_service = TimeEntryCache()

        # Start timer - should create in both cache and database
        response = self.client.post(
            reverse('time_tracking:timer-start'),
            data=json.dumps({'task_id': self.task.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        timer_id = response.json()['id']

        # Verify in database
        timer_db = TimeEntry.objects.get(id=timer_id)
        self.assertTrue(timer_db.is_running)

        # Verify in cache
        timer_cache = cache_service.get_active_timer(self.user.id)
        self.assertIsNotNone(timer_cache)
        self.assertEqual(timer_cache['id'], timer_id)

        # Stop timer - should update both cache and database
        response = self.client.post(
            reverse('time_tracking:timer-stop'),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Verify database updated
        timer_db.refresh_from_db()
        self.assertFalse(timer_db.is_running)
        self.assertIsNotNone(timer_db.end_time)

        # Verify cache cleared
        timer_cache = cache_service.get_active_timer(self.user.id)
        self.assertIsNone(timer_cache)

    def test_cache_fallback_to_database(self):
        """Test that system falls back to database when cache unavailable."""
        # Create running timer directly in database
        timer = TimeEntry.objects.create(
            user=self.user,
            task=self.task,
            start_time=timezone.now(),
            duration=timedelta(0),
            is_running=True
        )

        # Mock Redis get to return None (simulate cache miss)
        cache_service = TimeEntryCache()
        with patch.object(cache_service.redis_client, 'get', return_value=None):
            # Get active timer should fallback to database
            response = self.client.get(reverse('time_tracking:timer-get-active'))
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['id'], timer.id)
            self.assertTrue(data['is_running'])


class TimeRoundingIntegrationTest(TestCase):
    """Test time rounding applies correctly across different scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=self.user
        )
        task_list = TaskList.objects.create(
            name='Test Project',
            workspace=workspace,
            created_by=self.user
        )
        self.task = Task.objects.create(
            title='Rounding Test Task',
            task_list=task_list,
            created_by=self.user,
            priority='P2'
        )

        # Set 15-minute rounding, round up
        UserTimePreferences.objects.create(
            user=self.user,
            rounding_interval=15,
            rounding_method='up'
        )

    def test_rounding_applies_on_timer_stop(self):
        """Test that rounding rules apply when stopping timer."""
        # Start timer
        start_time = timezone.now() - timedelta(minutes=37)  # 37 minutes ago
        timer = TimeEntry.objects.create(
            user=self.user,
            task=self.task,
            start_time=start_time,
            duration=timedelta(0),
            is_running=True
        )

        # Store timer in cache
        cache_service = TimeEntryCache()
        cache_service.set_active_timer(self.user.id, {
            'id': timer.id,
            'task_id': self.task.id,
            'start_time': start_time.isoformat()
        })

        # Stop timer
        response = self.client.post(
            reverse('time_tracking:timer-stop'),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Verify duration rounded up to 45 minutes (3 x 15-minute intervals)
        timer.refresh_from_db()
        expected_rounded = timedelta(minutes=45)
        self.assertEqual(timer.duration, expected_rounded)

    def test_rounding_applies_on_manual_entry(self):
        """Test that rounding rules apply to manual entries."""
        # Create manual entry with 22 minutes (should round up to 30)
        response = self.client.post(
            reverse('time_tracking:time-entry-create'),
            data=json.dumps({
                'task_id': self.task.id,
                'duration': 22 * 60,  # 22 minutes in seconds
                'description': 'Rounding test'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        # Verify duration rounded up to 30 minutes
        entry = TimeEntry.objects.get(id=response.json()['id'])
        expected_rounded = timedelta(minutes=30)
        self.assertEqual(entry.duration, expected_rounded)


class BillableRateIntegrationTest(TestCase):
    """Test billable rate and revenue calculation."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=self.user
        )
        task_list = TaskList.objects.create(
            name='Test Project',
            workspace=workspace,
            created_by=self.user
        )
        self.task = Task.objects.create(
            title='Billable Task',
            task_list=task_list,
            created_by=self.user,
            priority='P1'
        )

        # Set user default rate
        UserTimePreferences.objects.create(
            user=self.user,
            default_billable_rate=100.0,
            default_currency='USD'
        )

    def test_user_default_rate_applied(self):
        """Test that user default billable rate is applied when specified."""
        # Create billable time entry
        response = self.client.post(
            reverse('time_tracking:time-entry-create'),
            data=json.dumps({
                'task_id': self.task.id,
                'duration': 3600,  # 1 hour
                'is_billable': True
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        # Verify rate applied
        entry = TimeEntry.objects.get(id=response.json()['id'])
        self.assertEqual(float(entry.billable_rate), 100.0)

    def test_revenue_calculation(self):
        """Test that revenue calculates correctly based on duration and rate."""
        # Create 2-hour billable entry at $150/hour
        TimeEntry.objects.create(
            user=self.user,
            task=self.task,
            duration=timedelta(hours=2),
            is_billable=True,
            billable_rate=150.0,
            currency='USD'
        )

        # Get list view and verify revenue displayed
        response = self.client.get(
            reverse('time_tracking:time-entry-list-html'),
            {'billable': 'billable'}
        )
        self.assertEqual(response.status_code, 200)
        # Expected revenue: 2 hours * $150 = $300
        self.assertContains(response, '$300')


class AuthorizationIntegrationTest(TestCase):
    """Test authorization across all time tracking endpoints."""

    def setUp(self):
        """Set up test fixtures with two users."""
        self.client = Client()

        # User 1
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        workspace1 = Workspace.objects.create(
            name='Workspace 1',
            owner=self.user1
        )
        task_list1 = TaskList.objects.create(
            name='Project 1',
            workspace=workspace1,
            created_by=self.user1
        )
        self.task1 = Task.objects.create(
            title='Task 1',
            task_list=task_list1,
            created_by=self.user1,
            priority='P1'
        )
        self.entry1 = TimeEntry.objects.create(
            user=self.user1,
            task=self.task1,
            duration=timedelta(hours=1)
        )

        # User 2
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        workspace2 = Workspace.objects.create(
            name='Workspace 2',
            owner=self.user2
        )
        task_list2 = TaskList.objects.create(
            name='Project 2',
            workspace=workspace2,
            created_by=self.user2
        )
        self.task2 = Task.objects.create(
            title='Task 2',
            task_list=task_list2,
            created_by=self.user2,
            priority='P2'
        )

    def test_user_cannot_access_other_users_entries(self):
        """Test that users can only access their own time entries."""
        # Login as user2
        self.client.login(username='user2', password='pass123')

        # Try to access user1's time entry
        response = self.client.get(
            reverse('time_tracking:time-entry-retrieve', kwargs={'entry_id': self.entry1.id})
        )
        # Should return 404 (not found) rather than 403 to avoid info disclosure
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_start_timer_on_other_users_task(self):
        """Test that users cannot start timer on tasks they don't have access to."""
        # Login as user2
        self.client.login(username='user2', password='pass123')

        # Try to start timer on user1's task
        response = self.client.post(
            reverse('time_tracking:timer-start'),
            data=json.dumps({'task_id': self.task1.id}),
            content_type='application/json'
        )
        # Should return error
        self.assertIn(response.status_code, [400, 403, 404])
