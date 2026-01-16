"""
Tests for time entry forms.

Tests cover three input modes, validation, and form submission.
Limited to 2-8 highly focused tests as per task requirements.
"""
import pytest
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from time_tracking.forms import TimeEntryForm
from time_tracking.models import TimeEntry, UserTimePreferences
from tasks.models import Task, TaskList
from accounts.models import Workspace


@pytest.mark.django_db
class TestTimeEntryForm:
    """Test suite for TimeEntryForm."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def workspace(self, user):
        """Create test workspace."""
        return Workspace.objects.create(
            name='Test Workspace',
            owner=user
        )

    @pytest.fixture
    def task_list(self, workspace, user):
        """Create test task list."""
        return TaskList.objects.create(
            name='Test Project',
            workspace=workspace,
            created_by=user
        )

    @pytest.fixture
    def task(self, task_list, user):
        """Create test task."""
        return Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user
        )

    @pytest.fixture
    def user_preferences(self, user):
        """Create user time preferences with rounding."""
        return UserTimePreferences.objects.create(
            user=user,
            rounding_interval=15,
            rounding_method='nearest'
        )

    def test_mode_a_start_and_end_time_calculates_duration(self, user, task):
        """Test Mode A: start_time + end_time calculates duration."""
        start_time = timezone.now() - timedelta(hours=2)
        end_time = timezone.now()

        form_data = {
            'task': task.id,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'description': 'Test entry',
        }

        form = TimeEntryForm(data=form_data, user=user)
        assert form.is_valid(), f"Form errors: {form.errors}"

        # Duration should be calculated from start_time and end_time
        cleaned_data = form.cleaned_data
        expected_duration = end_time - start_time
        # Allow small delta due to time precision
        assert abs(cleaned_data['duration'].total_seconds() - expected_duration.total_seconds()) < 1

    def test_mode_b_start_time_and_duration_calculates_end_time(self, user, task):
        """Test Mode B: start_time + duration calculates end_time."""
        start_time = timezone.now() - timedelta(hours=2)
        duration = timedelta(hours=1, minutes=30)

        form_data = {
            'task': task.id,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_input': '1:30',  # HH:MM format
            'description': 'Test entry',
        }

        form = TimeEntryForm(data=form_data, user=user)
        assert form.is_valid(), f"Form errors: {form.errors}"

        # End time should be calculated from start_time + duration
        cleaned_data = form.cleaned_data
        expected_end_time = start_time + duration
        assert abs((cleaned_data['end_time'] - expected_end_time).total_seconds()) < 1

    def test_mode_c_duration_only_leaves_times_null(self, user, task):
        """Test Mode C: duration only leaves start_time and end_time null."""
        form_data = {
            'task': task.id,
            'duration_input': '2:15',  # HH:MM format
            'description': 'Test entry',
        }

        form = TimeEntryForm(data=form_data, user=user)
        assert form.is_valid(), f"Form errors: {form.errors}"

        cleaned_data = form.cleaned_data
        assert cleaned_data['start_time'] is None
        assert cleaned_data['end_time'] is None
        assert cleaned_data['duration'] == timedelta(hours=2, minutes=15)

    def test_validation_end_time_before_start_time_rejected(self, user, task):
        """Test that end_time before start_time is rejected."""
        start_time = timezone.now()
        end_time = start_time - timedelta(hours=1)  # End before start

        form_data = {
            'task': task.id,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'description': 'Test entry',
        }

        form = TimeEntryForm(data=form_data, user=user)
        assert not form.is_valid()
        assert 'end_time' in form.errors or '__all__' in form.errors

    def test_validation_negative_duration_rejected(self, user, task):
        """Test that negative duration is rejected."""
        form_data = {
            'task': task.id,
            'duration_input': '-1:30',  # Negative duration
            'description': 'Test entry',
        }

        form = TimeEntryForm(data=form_data, user=user)
        assert not form.is_valid()
        assert 'duration_input' in form.errors or '__all__' in form.errors

    def test_form_applies_time_rounding(self, user, task, user_preferences):
        """Test that form applies time rounding from user preferences."""
        # Create entry with duration that should be rounded
        # User has 15-minute rounding with 'nearest' method
        form_data = {
            'task': task.id,
            'duration_input': '1:23',  # 1 hour 23 minutes should round to 1:30
            'description': 'Test entry',
        }

        form = TimeEntryForm(data=form_data, user=user)
        assert form.is_valid(), f"Form errors: {form.errors}"

        cleaned_data = form.cleaned_data
        # 1:23 (83 minutes) rounded to nearest 15 minutes = 1:30 (90 minutes)
        assert cleaned_data['duration'] == timedelta(hours=1, minutes=30)

    def test_form_submission_creates_time_entry(self, user, task):
        """Test that valid form saves time entry correctly."""
        start_time = timezone.now() - timedelta(hours=2)
        end_time = timezone.now()

        form_data = {
            'task': task.id,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'description': 'Completed work on feature',
            'is_billable': True,
            'billable_rate': '75.00',
            'currency': 'USD',
        }

        form = TimeEntryForm(data=form_data, user=user)
        assert form.is_valid(), f"Form errors: {form.errors}"

        # Save the form
        time_entry = form.save()

        # Verify time entry created correctly
        assert time_entry.id is not None
        assert time_entry.user == user
        assert time_entry.task == task
        assert time_entry.project == task.task_list
        assert time_entry.is_billable is True
        assert time_entry.billable_rate == 75.00
        assert time_entry.description == 'Completed work on feature'
        assert time_entry.is_running is False
