"""
Tests for Tag model validation and functionality.
"""
import pytest
from django.core.exceptions import ValidationError
from tasks.models import Tag


@pytest.mark.django_db
class TestTagModel:
    """Test suite for Tag model validation and methods."""

    def test_tag_creation_with_valid_data(self, user, workspace):
        """Test creating a tag with valid data."""
        tag = Tag.objects.create(
            name='work',
            workspace=workspace,
            created_by=user,
            color='#3B82F6'
        )

        assert tag.name == 'work'
        assert tag.workspace == workspace
        assert tag.created_by == user
        assert tag.color == '#3B82F6'

    def test_tag_name_required(self, user, workspace):
        """Test that tag name is required."""
        tag = Tag(
            name='',
            workspace=workspace,
            created_by=user
        )

        with pytest.raises(ValidationError) as exc_info:
            tag.save()

        assert 'name' in exc_info.value.message_dict

    def test_tag_name_unique_per_workspace(self, user, workspace):
        """Test that tag names are unique within a workspace."""
        # Create first tag
        Tag.objects.create(
            name='urgent',
            workspace=workspace,
            created_by=user
        )

        # Try to create duplicate tag in same workspace
        # Since our Tag model calls full_clean() in save(), it raises ValidationError
        with pytest.raises(ValidationError):
            Tag.objects.create(
                name='urgent',
                workspace=workspace,
                created_by=user
            )

    def test_tag_name_can_duplicate_across_workspaces(self, user, user2, workspace, workspace2):
        """Test that same tag name can exist in different workspaces."""
        # Create tag in first workspace
        tag1 = Tag.objects.create(
            name='important',
            workspace=workspace,
            created_by=user
        )

        # Create same tag name in second workspace - should work
        tag2 = Tag.objects.create(
            name='important',
            workspace=workspace2,
            created_by=user2
        )

        assert tag1.name == tag2.name
        assert tag1.workspace != tag2.workspace

    def test_tag_name_normalized_to_lowercase(self, user, workspace):
        """Test that tag names are normalized to lowercase."""
        tag = Tag(
            name='URGENT',
            workspace=workspace,
            created_by=user
        )
        tag.save()

        # Name should be lowercased
        assert tag.name == 'urgent'

    def test_tag_color_hex_validation(self, user, workspace):
        """Test that tag color must be valid hex format."""
        tag = Tag(
            name='test',
            workspace=workspace,
            created_by=user,
            color='invalid'
        )

        with pytest.raises(ValidationError) as exc_info:
            tag.save()

        assert 'color' in exc_info.value.message_dict

    def test_tag_color_default_value(self, user, workspace):
        """Test that tag has default color if not specified."""
        tag = Tag.objects.create(
            name='defaultcolor',
            workspace=workspace,
            created_by=user
        )

        assert tag.color == '#3B82F6'  # Default blue

    def test_tag_str_method(self, user, workspace):
        """Test tag string representation."""
        tag = Tag.objects.create(
            name='testing',
            workspace=workspace,
            created_by=user
        )

        assert str(tag) == 'testing'

    def test_tag_whitespace_trimmed(self, user, workspace):
        """Test that whitespace is trimmed from tag name."""
        tag = Tag(
            name='  urgent  ',
            workspace=workspace,
            created_by=user
        )
        tag.save()

        assert tag.name == 'urgent'

    def test_task_can_have_multiple_tags(self, user, task_list):
        """Test that a task can have multiple tags."""
        from tasks.models import Task

        task = Task.objects.create(
            title='Test Task with Tags',
            priority='P2',
            task_list=task_list,
            created_by=user
        )

        # Create tags
        tag1 = Tag.objects.create(name='work', workspace=task_list.workspace, created_by=user)
        tag2 = Tag.objects.create(name='urgent', workspace=task_list.workspace, created_by=user)
        tag3 = Tag.objects.create(name='client-a', workspace=task_list.workspace, created_by=user)

        # Add tags to task
        task.tags.add(tag1, tag2, tag3)

        # Verify tags were added
        assert task.tags.count() == 3
        assert tag1 in task.tags.all()
        assert tag2 in task.tags.all()
        assert tag3 in task.tags.all()

    def test_tag_can_be_used_by_multiple_tasks(self, user, task_list):
        """Test that a tag can be assigned to multiple tasks."""
        from tasks.models import Task

        tag = Tag.objects.create(name='urgent', workspace=task_list.workspace, created_by=user)

        task1 = Task.objects.create(title='Task 1', priority='P1', task_list=task_list, created_by=user)
        task2 = Task.objects.create(title='Task 2', priority='P1', task_list=task_list, created_by=user)
        task3 = Task.objects.create(title='Task 3', priority='P1', task_list=task_list, created_by=user)

        # Add same tag to multiple tasks
        task1.tags.add(tag)
        task2.tags.add(tag)
        task3.tags.add(tag)

        # Verify tag is associated with all tasks
        assert tag.tasks.count() == 3
        assert task1 in tag.tasks.all()
        assert task2 in tag.tasks.all()
        assert task3 in tag.tasks.all()


@pytest.mark.django_db
class TestTagManager:
    """Test suite for TagManager custom methods."""

    def test_for_workspace(self, user, workspace, workspace2):
        """Test TagManager.for_workspace() method."""
        # Create tags in different workspaces
        tag1 = Tag.objects.create(name='tag1', workspace=workspace, created_by=user)
        tag2 = Tag.objects.create(name='tag2', workspace=workspace, created_by=user)
        tag3 = Tag.objects.create(name='tag3', workspace=workspace2, created_by=user)

        # Query tags for workspace
        tags = Tag.objects.for_workspace(workspace)

        assert tags.count() == 2
        assert tag1 in tags
        assert tag2 in tags
        assert tag3 not in tags

    def test_get_or_create_tag_creates_new(self, user, workspace):
        """Test get_or_create_tag creates new tag if doesn't exist."""
        tag = Tag.objects.get_or_create_tag('newtag', workspace, user)

        assert tag is not None
        assert tag.name == 'newtag'
        assert tag.workspace == workspace
        assert tag.created_by == user

    def test_get_or_create_tag_returns_existing(self, user, workspace):
        """Test get_or_create_tag returns existing tag."""
        # Create tag first
        existing_tag = Tag.objects.create(name='existing', workspace=workspace, created_by=user)

        # Try to get or create same tag
        tag = Tag.objects.get_or_create_tag('existing', workspace, user)

        assert tag.id == existing_tag.id
        assert Tag.objects.filter(name='existing', workspace=workspace).count() == 1

    def test_get_or_create_tag_normalizes_name(self, user, workspace):
        """Test get_or_create_tag normalizes tag name."""
        tag = Tag.objects.get_or_create_tag('  UPPERCASE  ', workspace, user)

        assert tag.name == 'uppercase'

    def test_get_or_create_tag_with_custom_color(self, user, workspace):
        """Test get_or_create_tag with custom color."""
        tag = Tag.objects.get_or_create_tag('colorful', workspace, user, color='#FF5733')

        assert tag.color == '#FF5733'

    def test_popular_for_workspace(self, user, workspace, task_list):
        """Test popular_for_workspace returns tags ordered by usage."""
        from tasks.models import Task

        # Create tags
        tag1 = Tag.objects.create(name='tag1', workspace=workspace, created_by=user)
        tag2 = Tag.objects.create(name='tag2', workspace=workspace, created_by=user)
        tag3 = Tag.objects.create(name='tag3', workspace=workspace, created_by=user)

        # Create tasks and assign tags (tag2 used most, tag3 least)
        for i in range(5):
            task = Task.objects.create(title=f'Task {i}', priority='P2', task_list=task_list, created_by=user)
            task.tags.add(tag2)

        for i in range(3):
            task = Task.objects.create(title=f'Task {i+5}', priority='P2', task_list=task_list, created_by=user)
            task.tags.add(tag1)

        task = Task.objects.create(title='Last Task', priority='P2', task_list=task_list, created_by=user)
        task.tags.add(tag3)

        # Get popular tags
        popular = Tag.objects.popular_for_workspace(workspace)

        assert popular[0] == tag2  # Most used (5 tasks)
        assert popular[1] == tag1  # Second (3 tasks)
        assert popular[2] == tag3  # Least (1 task)
