"""
Tests for time entry list view and filtering functionality.

Tests critical behaviors:
- Default week view displays correctly
- Date range filters work
- Project/task filters work
- Billable filter works
- Daily and grand totals calculate correctly
"""
import pytest
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.contrib.auth.models import User
from tasks.models import Task, TaskList, Tag
from accounts.models import Workspace
from time_tracking.models import TimeEntry, TimeEntryTag


@pytest.fixture
def user(db):
    """Create test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def workspace(db, user):
    """Create test workspace."""
    return Workspace.objects.create(
        name='Test Workspace',
        owner=user
    )


@pytest.fixture
def project(db, workspace, user):
    """Create test project (task list)."""
    return TaskList.objects.create(
        name='Test Project',
        workspace=workspace,
        created_by=user
    )


@pytest.fixture
def task1(db, project, user):
    """Create first test task."""
    return Task.objects.create(
        title='Test Task 1',
        priority='P2',
        task_list=project,
        created_by=user
    )


@pytest.fixture
def task2(db, project, user):
    """Create second test task."""
    return Task.objects.create(
        title='Test Task 2',
        priority='P2',
        task_list=project,
        created_by=user
    )


@pytest.fixture
def tag1(db, workspace, user):
    """Create first test tag."""
    return Tag.objects.create(
        name='urgent',
        workspace=workspace,
        created_by=user,
        color='#FF0000'
    )


@pytest.fixture
def tag2(db, workspace, user):
    """Create second test tag."""
    return Tag.objects.create(
        name='development',
        workspace=workspace,
        created_by=user,
        color='#00FF00'
    )


@pytest.mark.django_db
class TestTimeEntryListFiltering:
    """Test time entry list view filtering functionality."""

    def test_default_current_week_filter(self, client, user, task1):
        """Test that default view shows current week entries."""
        # Log in user
        client.force_login(user)

        # Create entries for different weeks
        today = timezone.now()
        monday = today - timedelta(days=today.weekday())  # Monday of current week
        last_week = monday - timedelta(days=7)
        next_week = monday + timedelta(days=7)

        # Current week entry
        current_entry = TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=monday,
            end_time=monday + timedelta(hours=2),
            duration=timedelta(hours=2),
            is_running=False
        )

        # Last week entry
        TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=last_week,
            end_time=last_week + timedelta(hours=1),
            duration=timedelta(hours=1),
            is_running=False
        )

        # Next week entry
        TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=next_week,
            end_time=next_week + timedelta(hours=1),
            duration=timedelta(hours=1),
            is_running=False
        )

        # Request list view with default filter (current week)
        response = client.get('/entries/')

        assert response.status_code == 200
        # Should only show current week entry
        entries = response.context['entries']
        assert len(entries) == 1
        assert entries[0].id == current_entry.id

    def test_custom_date_range_filter(self, client, user, task1):
        """Test custom date range filtering."""
        client.force_login(user)

        # Create entries across multiple days
        base_date = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)

        entry1 = TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=base_date - timedelta(days=10),
            end_time=base_date - timedelta(days=10, hours=-2),
            duration=timedelta(hours=2),
            is_running=False
        )

        entry2 = TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=base_date - timedelta(days=5),
            end_time=base_date - timedelta(days=5, hours=-3),
            duration=timedelta(hours=3),
            is_running=False
        )

        entry3 = TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=base_date - timedelta(days=2),
            end_time=base_date - timedelta(days=2, hours=-1),
            duration=timedelta(hours=1),
            is_running=False
        )

        # Filter for specific date range (last 7 days)
        start_date = (base_date - timedelta(days=7)).date()
        end_date = base_date.date()

        response = client.get(
            '/entries/',
            {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()}
        )

        assert response.status_code == 200
        entries = response.context['entries']
        # Should only show entries within date range (entry2 and entry3)
        assert len(entries) == 2
        entry_ids = [e.id for e in entries]
        assert entry2.id in entry_ids
        assert entry3.id in entry_ids
        assert entry1.id not in entry_ids

    def test_project_filter(self, client, user, workspace):
        """Test filtering by project."""
        client.force_login(user)

        # Create two projects
        project1 = TaskList.objects.create(name='Project 1', workspace=workspace, created_by=user)
        project2 = TaskList.objects.create(name='Project 2', workspace=workspace, created_by=user)

        task1 = Task.objects.create(title='Task 1', priority='P2', task_list=project1, created_by=user)
        task2 = Task.objects.create(title='Task 2', priority='P2', task_list=project2, created_by=user)

        # Create entries for both projects
        entry1 = TimeEntry.objects.create(
            user=user,
            task=task1,
            project=project1,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            duration=timedelta(hours=2),
            is_running=False
        )

        entry2 = TimeEntry.objects.create(
            user=user,
            task=task2,
            project=project2,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            duration=timedelta(hours=1),
            is_running=False
        )

        # Filter by project1
        response = client.get('/entries/', {'project_id': project1.id})

        assert response.status_code == 200
        entries = response.context['entries']
        assert len(entries) == 1
        assert entries[0].id == entry1.id

    def test_task_filter(self, client, user, task1, task2):
        """Test filtering by task."""
        client.force_login(user)

        # Create entries for different tasks
        entry1 = TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            duration=timedelta(hours=2),
            is_running=False
        )

        entry2 = TimeEntry.objects.create(
            user=user,
            task=task2,
            project=task2.task_list,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            duration=timedelta(hours=1),
            is_running=False
        )

        # Filter by task1
        response = client.get('/entries/', {'task_id': task1.id})

        assert response.status_code == 200
        entries = response.context['entries']
        assert len(entries) == 1
        assert entries[0].id == entry1.id

    def test_billable_filter(self, client, user, task1):
        """Test filtering by billable status."""
        client.force_login(user)

        # Create billable and non-billable entries
        billable_entry = TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            duration=timedelta(hours=2),
            is_billable=True,
            billable_rate=50.00,
            is_running=False
        )

        non_billable_entry = TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            duration=timedelta(hours=1),
            is_billable=False,
            is_running=False
        )

        # Filter for billable only
        response = client.get('/entries/', {'billable': 'true'})

        assert response.status_code == 200
        entries = response.context['entries']
        assert len(entries) == 1
        assert entries[0].id == billable_entry.id

        # Filter for non-billable only
        response = client.get('/entries/', {'billable': 'false'})

        assert response.status_code == 200
        entries = response.context['entries']
        assert len(entries) == 1
        assert entries[0].id == non_billable_entry.id

    def test_tags_filter(self, client, user, task1, tag1, tag2):
        """Test filtering by tags (OR logic)."""
        client.force_login(user)

        # Create entries with different tags
        entry1 = TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            duration=timedelta(hours=2),
            is_running=False
        )
        TimeEntryTag.objects.create(time_entry=entry1, tag=tag1)

        entry2 = TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            duration=timedelta(hours=1),
            is_running=False
        )
        TimeEntryTag.objects.create(time_entry=entry2, tag=tag2)

        entry3 = TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=3),
            duration=timedelta(hours=3),
            is_running=False
        )
        # No tags for entry3

        # Filter by tag1 (should get entry1)
        response = client.get('/entries/', {'tags': str(tag1.id)})

        assert response.status_code == 200
        entries = response.context['entries']
        assert len(entries) == 1
        assert entries[0].id == entry1.id

        # Filter by both tags (should get entry1 and entry2 - OR logic)
        response = client.get('/entries/', {'tags': f'{tag1.id},{tag2.id}'})

        assert response.status_code == 200
        entries = response.context['entries']
        assert len(entries) == 2
        entry_ids = [e.id for e in entries]
        assert entry1.id in entry_ids
        assert entry2.id in entry_ids

    def test_daily_and_grand_totals(self, client, user, task1):
        """Test that daily subtotals and grand total calculate correctly."""
        client.force_login(user)

        # Create entries across multiple days
        today = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)

        # Today's entries: 2 hours + 3 hours = 5 hours
        TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=today,
            end_time=today + timedelta(hours=2),
            duration=timedelta(hours=2),
            is_running=False
        )

        TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=today + timedelta(hours=3),
            end_time=today + timedelta(hours=6),
            duration=timedelta(hours=3),
            is_running=False
        )

        # Yesterday's entries: 4 hours
        TimeEntry.objects.create(
            user=user,
            task=task1,
            project=task1.task_list,
            start_time=yesterday,
            end_time=yesterday + timedelta(hours=4),
            duration=timedelta(hours=4),
            is_running=False
        )

        response = client.get('/entries/')

        assert response.status_code == 200

        # Check daily totals
        daily_totals = response.context['daily_totals']
        assert len(daily_totals) == 2

        # Check grand total (should be 9 hours)
        grand_total = response.context['grand_total']
        assert grand_total == timedelta(hours=9)

    def test_filters_persist_in_url(self, client, user, task1, project):
        """Test that applied filters persist in URL query parameters."""
        client.force_login(user)

        TimeEntry.objects.create(
            user=user,
            task=task1,
            project=project,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            duration=timedelta(hours=2),
            is_billable=True,
            is_running=False
        )

        # Apply multiple filters
        response = client.get('/entries/', {
            'project_id': project.id,
            'task_id': task1.id,
            'billable': 'true',
        })

        assert response.status_code == 200

        # Check that query params are available in context for template
        assert response.context['filters']['project_id'] == str(project.id)
        assert response.context['filters']['task_id'] == str(task1.id)
        assert response.context['filters']['billable'] == 'true'
