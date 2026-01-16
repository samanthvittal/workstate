"""
Tests for analytics dashboard calculations and export functionality.

Focuses on critical analytics calculations: total hours, billable hours,
revenue, time-of-day patterns, and export functionality.
"""
import pytest
from datetime import datetime, timedelta, date, time
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

from accounts.models import Workspace
from tasks.models import Task, TaskList, Tag
from time_tracking.models import TimeEntry, TimeEntryTag
from time_tracking.services.analytics import AnalyticsService


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
def task_list(db, workspace, user):
    """Create test task list (project)."""
    return TaskList.objects.create(
        name='Test Project',
        workspace=workspace,
        created_by=user
    )


@pytest.fixture
def task(db, task_list, user):
    """Create test task."""
    return Task.objects.create(
        priority="P3",
        title='Test Task',
        task_list=task_list,
        created_by=user
    )


@pytest.fixture
def analytics_service(db, user):
    """Create analytics service instance."""
    return AnalyticsService(user)


@pytest.mark.django_db
class TestAnalyticsSummaryStatistics:
    """Test summary statistics calculations."""

    def test_total_hours_today(self, user, task, analytics_service):
        """Test calculation of total hours today."""
        today = timezone.now().date()

        # Create time entries for today
        TimeEntry.objects.create(
            user=user,
            task=task,
            duration=timedelta(hours=2),
            start_time=timezone.make_aware(datetime.combine(today, time(9, 0))),
            end_time=timezone.make_aware(datetime.combine(today, time(11, 0))),
            is_running=False
        )

        TimeEntry.objects.create(
            user=user,
            task=task,
            duration=timedelta(hours=3),
            start_time=timezone.make_aware(datetime.combine(today, time(13, 0))),
            end_time=timezone.make_aware(datetime.combine(today, time(16, 0))),
            is_running=False
        )

        # Calculate summary
        summary = analytics_service.get_summary_statistics(today, today)

        assert summary['total_hours'] == timedelta(hours=5)
        assert summary['total_entries'] == 2

    def test_billable_vs_non_billable_hours(self, user, task, analytics_service):
        """Test calculation of billable vs non-billable hours."""
        today = timezone.now().date()

        # Create billable entry
        TimeEntry.objects.create(
            user=user,
            task=task,
            duration=timedelta(hours=4),
            start_time=timezone.make_aware(datetime.combine(today, time(9, 0))),
            is_running=False,
            is_billable=True,
            billable_rate=Decimal('50.00')
        )

        # Create non-billable entry
        TimeEntry.objects.create(
            user=user,
            task=task,
            duration=timedelta(hours=2),
            start_time=timezone.make_aware(datetime.combine(today, time(14, 0))),
            is_running=False,
            is_billable=False
        )

        summary = analytics_service.get_summary_statistics(today, today)

        assert summary['billable_hours'] == timedelta(hours=4)
        assert summary['non_billable_hours'] == timedelta(hours=2)
        assert summary['total_revenue'] == Decimal('200.00')  # 4 hours * $50

    def test_project_breakdown(self, user, workspace, analytics_service):
        """Test project breakdown calculations."""
        today = timezone.now().date()

        # Create two projects
        project1 = TaskList.objects.create(name='Project 1', workspace=workspace, created_by=user)
        project2 = TaskList.objects.create(name='Project 2', workspace=workspace, created_by=user)

        task1 = Task.objects.create(priority="P3", title='Task 1', task_list=project1, created_by=user)
        task2 = Task.objects.create(priority="P3", title='Task 2', task_list=project2, created_by=user)

        # Create time entries
        TimeEntry.objects.create(
            user=user,
            task=task1,
            project=project1,
            duration=timedelta(hours=3),
            start_time=timezone.make_aware(datetime.combine(today, time(9, 0))),
            is_running=False
        )

        TimeEntry.objects.create(
            user=user,
            task=task2,
            project=project2,
            duration=timedelta(hours=5),
            start_time=timezone.make_aware(datetime.combine(today, time(13, 0))),
            is_running=False
        )

        breakdown = analytics_service.get_project_breakdown(today, today)

        assert len(breakdown) == 2
        assert breakdown[0]['project_name'] == 'Project 2'
        assert breakdown[0]['total_duration'] == timedelta(hours=5)
        assert breakdown[1]['project_name'] == 'Project 1'
        assert breakdown[1]['total_duration'] == timedelta(hours=3)

    def test_time_of_day_heatmap(self, user, task, analytics_service):
        """Test time-of-day heatmap calculations."""
        today = timezone.now().date()

        # Create entries at different times
        TimeEntry.objects.create(
            user=user,
            task=task,
            duration=timedelta(hours=2),
            start_time=timezone.make_aware(datetime.combine(today, time(9, 0))),
            end_time=timezone.make_aware(datetime.combine(today, time(11, 0))),
            is_running=False
        )

        TimeEntry.objects.create(
            user=user,
            task=task,
            duration=timedelta(hours=3),
            start_time=timezone.make_aware(datetime.combine(today, time(14, 0))),
            end_time=timezone.make_aware(datetime.combine(today, time(17, 0))),
            is_running=False
        )

        heatmap = analytics_service.get_time_of_day_heatmap(today, today)

        # Check that hours 9-10 and 14-16 have data
        assert heatmap[9] > timedelta(0)
        assert heatmap[10] > timedelta(0)
        assert heatmap[14] > timedelta(0)
        assert heatmap[15] > timedelta(0)
        assert heatmap[16] > timedelta(0)

        # Check that other hours are zero
        assert heatmap[0] == timedelta(0)
        assert heatmap[23] == timedelta(0)


@pytest.mark.django_db
class TestAnalyticsExport:
    """Test export functionality."""

    def test_csv_export_data_structure(self, user, task, analytics_service):
        """Test CSV export returns correct data structure."""
        today = timezone.now().date()

        TimeEntry.objects.create(
            user=user,
            task=task,
            duration=timedelta(hours=2),
            start_time=timezone.make_aware(datetime.combine(today, time(9, 0))),
            end_time=timezone.make_aware(datetime.combine(today, time(11, 0))),
            is_running=False,
            description='Test entry'
        )

        csv_data = analytics_service.get_csv_export_data(today, today)

        assert len(csv_data) == 1
        assert csv_data[0]['task'] == 'Test Task'
        assert csv_data[0]['duration'] == timedelta(hours=2)
        assert 'date' in csv_data[0]
        assert 'description' in csv_data[0]
