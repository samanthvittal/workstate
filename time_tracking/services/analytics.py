"""
Analytics service for calculating time tracking statistics and breakdowns.

Provides methods for summary statistics, project/task/tag breakdowns,
time-of-day heatmaps, day-of-week patterns, and export data preparation.
"""
import logging
from datetime import datetime, timedelta, time
from decimal import Decimal
from collections import defaultdict
from django.db.models import Sum, Count, Q
from django.utils import timezone

from time_tracking.models import TimeEntry, TimeEntryTag

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Service for calculating analytics and generating reports.

    Handles all analytics calculations for time tracking data including
    summary statistics, breakdowns by dimension, and time patterns.
    """

    def __init__(self, user):
        """
        Initialize analytics service for a specific user.

        Args:
            user: User instance to calculate analytics for
        """
        self.user = user

    def get_summary_statistics(self, start_date, end_date):
        """
        Calculate summary statistics for a date range.

        Args:
            start_date: Start date (date object)
            end_date: End date (date object)

        Returns:
            dict: Summary statistics including total hours, billable hours, revenue, etc.
        """
        entries = self._get_entries_in_range(start_date, end_date)

        # Calculate total hours
        total_duration = timedelta(0)
        billable_duration = timedelta(0)
        non_billable_duration = timedelta(0)
        total_revenue = Decimal('0.00')
        entry_count = 0

        for entry in entries:
            if entry.duration:
                total_duration += entry.duration
                entry_count += 1

                if entry.is_billable:
                    billable_duration += entry.duration
                    if entry.billable_rate:
                        hours = Decimal(str(entry.duration.total_seconds() / 3600))
                        total_revenue += hours * entry.billable_rate
                else:
                    non_billable_duration += entry.duration

        return {
            'total_hours': total_duration,
            'billable_hours': billable_duration,
            'non_billable_hours': non_billable_duration,
            'total_revenue': total_revenue,
            'total_entries': entry_count,
            'start_date': start_date,
            'end_date': end_date,
        }

    def get_project_breakdown(self, start_date, end_date):
        """
        Calculate time spent per project.

        Args:
            start_date: Start date (date object)
            end_date: End date (date object)

        Returns:
            list: List of dicts with project_id, project_name, total_duration
                  sorted by duration DESC
        """
        entries = self._get_entries_in_range(start_date, end_date)

        # Group by project
        project_totals = defaultdict(lambda: {'duration': timedelta(0), 'count': 0})

        for entry in entries:
            if entry.project:
                project_id = entry.project.id
                project_name = entry.project.name
                project_totals[project_id]['project_id'] = project_id
                project_totals[project_id]['project_name'] = project_name
                if entry.duration:
                    project_totals[project_id]['duration'] += entry.duration
                project_totals[project_id]['count'] += 1

        # Convert to list and sort by duration
        breakdown = [
            {
                'project_id': data['project_id'],
                'project_name': data['project_name'],
                'total_duration': data['duration'],
                'entry_count': data['count'],
            }
            for project_id, data in project_totals.items()
        ]

        # Sort by duration descending
        breakdown.sort(key=lambda x: x['total_duration'], reverse=True)

        return breakdown

    def get_task_breakdown(self, start_date, end_date, limit=10):
        """
        Calculate time spent per task (top N tasks).

        Args:
            start_date: Start date (date object)
            end_date: End date (date object)
            limit: Maximum number of tasks to return (default: 10)

        Returns:
            list: List of dicts with task_id, task_name, project_name, total_duration
                  sorted by duration DESC, limited to top N
        """
        entries = self._get_entries_in_range(start_date, end_date)

        # Group by task
        task_totals = defaultdict(lambda: {'duration': timedelta(0), 'count': 0})

        for entry in entries:
            task_id = entry.task.id
            task_title = entry.task.title
            project_name = entry.project.name if entry.project else 'No Project'

            task_totals[task_id]['task_id'] = task_id
            task_totals[task_id]['task_name'] = task_title
            task_totals[task_id]['project_name'] = project_name
            if entry.duration:
                task_totals[task_id]['duration'] += entry.duration
            task_totals[task_id]['count'] += 1

        # Convert to list and sort by duration
        breakdown = [
            {
                'task_id': data['task_id'],
                'task_name': data['task_name'],
                'project_name': data['project_name'],
                'total_duration': data['duration'],
                'entry_count': data['count'],
            }
            for task_id, data in task_totals.items()
        ]

        # Sort by duration descending and limit
        breakdown.sort(key=lambda x: x['total_duration'], reverse=True)

        return breakdown[:limit]

    def get_tag_breakdown(self, start_date, end_date):
        """
        Calculate time spent per tag.

        Args:
            start_date: Start date (date object)
            end_date: End date (date object)

        Returns:
            list: List of dicts with tag_id, tag_name, total_duration
                  sorted by duration DESC
        """
        entries = self._get_entries_in_range(start_date, end_date)
        entry_ids = [entry.id for entry in entries]

        # Get all tags for these entries
        tag_entries = TimeEntryTag.objects.filter(
            time_entry_id__in=entry_ids
        ).select_related('tag', 'time_entry')

        # Group by tag
        tag_totals = defaultdict(lambda: {'duration': timedelta(0), 'count': 0})

        for tag_entry in tag_entries:
            tag_id = tag_entry.tag.id
            tag_name = tag_entry.tag.name

            tag_totals[tag_id]['tag_id'] = tag_id
            tag_totals[tag_id]['tag_name'] = tag_name
            if tag_entry.time_entry.duration:
                tag_totals[tag_id]['duration'] += tag_entry.time_entry.duration
            tag_totals[tag_id]['count'] += 1

        # Convert to list and sort by duration
        breakdown = [
            {
                'tag_id': data['tag_id'],
                'tag_name': data['tag_name'],
                'total_duration': data['duration'],
                'entry_count': data['count'],
            }
            for tag_id, data in tag_totals.items()
        ]

        # Sort by duration descending
        breakdown.sort(key=lambda x: x['total_duration'], reverse=True)

        return breakdown

    def get_time_of_day_heatmap(self, start_date, end_date):
        """
        Calculate time entries by hour of day (0-23).

        Args:
            start_date: Start date (date object)
            end_date: End date (date object)

        Returns:
            dict: Dictionary with hour (0-23) as key and total duration as value
        """
        entries = self._get_entries_in_range(start_date, end_date)

        # Initialize all hours to zero
        heatmap = {hour: timedelta(0) for hour in range(24)}

        for entry in entries:
            if entry.start_time and entry.end_time and entry.duration:
                # Calculate duration for each hour this entry spans
                current_time = entry.start_time
                end_time = entry.end_time

                while current_time < end_time:
                    hour = current_time.hour
                    next_hour = current_time.replace(
                        minute=0, second=0, microsecond=0
                    ) + timedelta(hours=1)

                    # Calculate duration in this hour
                    hour_end = min(next_hour, end_time)
                    duration_in_hour = hour_end - current_time

                    heatmap[hour] += duration_in_hour
                    current_time = next_hour

        return heatmap

    def get_day_of_week_patterns(self, start_date, end_date):
        """
        Calculate average hours per day of week (Monday=0 to Sunday=6).

        Args:
            start_date: Start date (date object)
            end_date: End date (date object)

        Returns:
            dict: Dictionary with day_of_week (0-6) as key and dict containing
                  total_duration, billable_duration, entry_count
        """
        entries = self._get_entries_in_range(start_date, end_date)

        # Initialize all days to zero
        patterns = {
            day: {
                'total_duration': timedelta(0),
                'billable_duration': timedelta(0),
                'non_billable_duration': timedelta(0),
                'entry_count': 0,
            }
            for day in range(7)
        }

        for entry in entries:
            # Get day of week from start_time or created_at
            if entry.start_time:
                day_of_week = entry.start_time.weekday()
            else:
                day_of_week = entry.created_at.weekday()

            if entry.duration:
                patterns[day_of_week]['total_duration'] += entry.duration
                patterns[day_of_week]['entry_count'] += 1

                if entry.is_billable:
                    patterns[day_of_week]['billable_duration'] += entry.duration
                else:
                    patterns[day_of_week]['non_billable_duration'] += entry.duration

        return patterns

    def get_csv_export_data(self, start_date, end_date):
        """
        Prepare data for CSV export.

        Args:
            start_date: Start date (date object)
            end_date: End date (date object)

        Returns:
            list: List of dicts with all time entry data formatted for CSV export
        """
        entries = self._get_entries_in_range(start_date, end_date)

        export_data = []

        for entry in entries:
            # Get entry date
            if entry.start_time:
                entry_date = entry.start_time.date()
                start_time_str = entry.start_time.strftime('%Y-%m-%d %H:%M:%S')
                end_time_str = entry.end_time.strftime('%Y-%m-%d %H:%M:%S') if entry.end_time else ''
            else:
                entry_date = entry.created_at.date()
                start_time_str = ''
                end_time_str = ''

            # Get tags
            tags = [tag.tag.name for tag in entry.time_entry_tags.all()]
            tags_str = ', '.join(tags) if tags else ''

            # Calculate revenue
            revenue = Decimal('0.00')
            if entry.is_billable and entry.billable_rate and entry.duration:
                hours = Decimal(str(entry.duration.total_seconds() / 3600))
                revenue = hours * entry.billable_rate

            export_data.append({
                'date': entry_date,
                'task': entry.task.title,
                'project': entry.project.name if entry.project else '',
                'duration': entry.duration,
                'start_time': start_time_str,
                'end_time': end_time_str,
                'description': entry.description or '',
                'tags': tags_str,
                'billable': 'Yes' if entry.is_billable else 'No',
                'rate': entry.billable_rate if entry.billable_rate else '',
                'currency': entry.currency if entry.is_billable else '',
                'revenue': revenue if entry.is_billable else '',
            })

        return export_data

    def _get_entries_in_range(self, start_date, end_date):
        """
        Get time entries for user in date range.

        Args:
            start_date: Start date (date object)
            end_date: End date (date object)

        Returns:
            QuerySet: Filtered time entries with related data
        """
        entries = TimeEntry.objects.filter(
            user=self.user,
            is_running=False
        ).filter(
            Q(start_time__date__gte=start_date, start_time__date__lte=end_date) |
            Q(start_time__isnull=True, created_at__date__gte=start_date, created_at__date__lte=end_date)
        ).select_related(
            'task',
            'project',
            'user'
        ).prefetch_related(
            'time_entry_tags__tag'
        ).order_by('-start_time', '-created_at')

        return list(entries)
