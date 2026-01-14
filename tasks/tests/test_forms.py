"""
Tests for TaskForm validation.
"""
import pytest
from django.contrib.auth.models import User
from tasks.forms import TaskForm
from accounts.models import Workspace


@pytest.mark.django_db
class TestTaskFormValidation:
    """Test suite for TaskForm validation rules."""

    @pytest.fixture
    def user(self):
        """Create a test user."""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def workspace(self, user):
        """Create a test workspace."""
        return Workspace.objects.create(
            name='Test Workspace',
            owner=user
        )

    def test_title_required_validation(self, workspace):
        """Test that title field is required."""
        form = TaskForm(data={
            'title': '',
            'priority': 'P1',
        })

        assert not form.is_valid()
        assert 'title' in form.errors

    def test_title_whitespace_validation(self, workspace):
        """Test that title cannot be only whitespace."""
        form = TaskForm(data={
            'title': '   ',
            'priority': 'P1',
        })

        assert not form.is_valid()
        assert 'title' in form.errors

    def test_priority_required_validation(self, workspace):
        """Test that priority field is required."""
        form = TaskForm(data={
            'title': 'Test Task',
            'priority': '',
        })

        assert not form.is_valid()
        assert 'priority' in form.errors

    def test_due_time_requires_due_date_validation(self, workspace):
        """Test that due_time cannot be set without due_date."""
        form = TaskForm(data={
            'title': 'Test Task',
            'priority': 'P2',
            'due_time': '14:30',
        })

        assert not form.is_valid()
        assert 'due_time' in form.errors or '__all__' in form.errors

    def test_valid_form_with_all_fields(self, workspace):
        """Test that form is valid with all fields properly filled."""
        form = TaskForm(data={
            'title': 'Complete Project',
            'description': 'This is a test description with markdown support',
            'due_date': '2026-12-31',
            'due_time': '17:00',
            'priority': 'P1',
            'status': 'active',
        })

        assert form.is_valid(), form.errors

    def test_valid_form_with_minimal_fields(self, workspace):
        """Test that form is valid with only required fields."""
        form = TaskForm(data={
            'title': 'Simple Task',
            'priority': 'P3',
        })

        assert form.is_valid(), form.errors

    def test_description_max_length_validation(self, workspace):
        """Test that description field enforces max length."""
        long_description = 'a' * 10001  # Exceeds 10,000 character limit
        form = TaskForm(data={
            'title': 'Test Task',
            'priority': 'P2',
            'description': long_description,
        })

        assert not form.is_valid()
        assert 'description' in form.errors

    def test_priority_choices_validation(self, workspace):
        """Test that priority must be one of P1/P2/P3/P4."""
        form = TaskForm(data={
            'title': 'Test Task',
            'priority': 'INVALID',
        })

        assert not form.is_valid()
        assert 'priority' in form.errors
