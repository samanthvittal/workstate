"""
Tests for TaskForm validation including tag input handling.
"""
import pytest
from django.core.exceptions import ValidationError
from tasks.forms import TaskForm
from tasks.models import Task, Tag


@pytest.mark.django_db
class TestTaskFormTagInput:
    """Test suite for TaskForm tag input validation."""

    def test_tags_input_parsed_from_comma_separated(self, user, task_list):
        """Test that comma-separated tags are parsed correctly."""
        form_data = {
            'title': 'Test Task with Tags',
            'priority': 'P2',
            'status': 'active',
            'tags_input': 'work, urgent, client-a',
        }
        form = TaskForm(data=form_data)

        assert form.is_valid()
        assert form.cleaned_data['tags_input'] == ['work', 'urgent', 'client-a']

    def test_tags_input_empty_tags_ignored(self, user, task_list):
        """Test that empty tag names are ignored."""
        form_data = {
            'title': 'Test Task',
            'priority': 'P2',
            'status': 'active',
            'tags_input': 'work, , urgent, , client-a',
        }
        form = TaskForm(data=form_data)

        assert form.is_valid()
        assert form.cleaned_data['tags_input'] == ['work', 'urgent', 'client-a']

    def test_tags_input_whitespace_only_ignored(self, user, task_list):
        """Test that whitespace-only tags are ignored."""
        form_data = {
            'title': 'Test Task',
            'priority': 'P2',
            'status': 'active',
            'tags_input': 'work,   , urgent,  ',
        }
        form = TaskForm(data=form_data)

        assert form.is_valid()
        assert form.cleaned_data['tags_input'] == ['work', 'urgent']

    def test_tags_input_duplicate_tags_removed(self, user, task_list):
        """Test that duplicate tags are removed (case-insensitive)."""
        form_data = {
            'title': 'Test Task',
            'priority': 'P2',
            'status': 'active',
            'tags_input': 'work, WORK, urgent, Work, urgent',
        }
        form = TaskForm(data=form_data)

        assert form.is_valid()
        # Should keep only first occurrence of each unique tag (case-insensitive)
        assert form.cleaned_data['tags_input'] == ['work', 'urgent']

    def test_tags_input_normalized_to_lowercase(self, user, task_list):
        """Test that all tag names are normalized to lowercase."""
        form_data = {
            'title': 'Test Task',
            'priority': 'P2',
            'status': 'active',
            'tags_input': 'WORK, Urgent, Client-A',
        }
        form = TaskForm(data=form_data)

        assert form.is_valid()
        assert form.cleaned_data['tags_input'] == ['work', 'urgent', 'client-a']

    def test_tags_input_max_limit_validation(self, user, task_list):
        """Test that max 20 tags are allowed per task."""
        # Create 21 tags
        tags = [f'tag{i}' for i in range(21)]
        form_data = {
            'title': 'Test Task',
            'priority': 'P2',
            'status': 'active',
            'tags_input': ', '.join(tags),
        }
        form = TaskForm(data=form_data)

        assert not form.is_valid()
        assert 'tags_input' in form.errors
        assert 'Maximum 20 tags allowed' in form.errors['tags_input'][0]

    def test_tags_input_individual_tag_length_validation(self, user, task_list):
        """Test that individual tags cannot exceed 50 characters."""
        long_tag = 'a' * 51  # 51 characters
        form_data = {
            'title': 'Test Task',
            'priority': 'P2',
            'status': 'active',
            'tags_input': f'work, {long_tag}, urgent',
        }
        form = TaskForm(data=form_data)

        assert not form.is_valid()
        assert 'tags_input' in form.errors
        assert 'exceeds maximum length' in form.errors['tags_input'][0]

    def test_tags_input_empty_string_returns_empty_list(self, user, task_list):
        """Test that empty tags_input returns empty list."""
        form_data = {
            'title': 'Test Task',
            'priority': 'P2',
            'status': 'active',
            'tags_input': '',
        }
        form = TaskForm(data=form_data)

        assert form.is_valid()
        assert form.cleaned_data['tags_input'] == []

    def test_tags_input_not_required(self, user, task_list):
        """Test that tags_input is not required (task can have no tags)."""
        form_data = {
            'title': 'Test Task',
            'priority': 'P2',
            'status': 'active',
            # No tags_input provided
        }
        form = TaskForm(data=form_data)

        assert form.is_valid()

    def test_tags_input_whitespace_trimmed(self, user, task_list):
        """Test that whitespace is trimmed from tag names."""
        form_data = {
            'title': 'Test Task',
            'priority': 'P2',
            'status': 'active',
            'tags_input': '  work  ,  urgent  ,  client-a  ',
        }
        form = TaskForm(data=form_data)

        assert form.is_valid()
        assert form.cleaned_data['tags_input'] == ['work', 'urgent', 'client-a']


@pytest.mark.django_db
class TestTaskFormTagPrePopulation:
    """Test suite for tag pre-population when editing tasks."""

    def test_tags_input_prepopulated_on_edit(self, user, task_list, workspace):
        """Test that tags_input is pre-populated with existing tags when editing."""
        # Create a task with tags
        task = Task.objects.create(
            title='Test Task',
            priority='P2',
            task_list=task_list,
            created_by=user
        )

        # Create and assign tags
        tag1 = Tag.objects.create(name='work', workspace=workspace, created_by=user)
        tag2 = Tag.objects.create(name='urgent', workspace=workspace, created_by=user)
        task.tags.add(tag1, tag2)

        # Create form with task instance
        form = TaskForm(instance=task)

        # Check that tags_input is pre-populated (tags ordered alphabetically by model)
        assert form.fields['tags_input'].initial == 'urgent, work'

    def test_tags_input_empty_on_create(self, user, task_list):
        """Test that tags_input is empty when creating a new task."""
        form = TaskForm()

        # tags_input should not have initial value for new task
        assert form.fields['tags_input'].initial is None
