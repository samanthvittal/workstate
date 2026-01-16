"""
Time entry list view with comprehensive filtering.

Provides HTML view for displaying time entries with filters for date ranges,
projects, tasks, tags, and billable status. Includes daily subtotals and grand totals.
"""
import logging
from datetime import datetime, timedelta, date
from itertools import groupby
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Prefetch
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from accounts.mixins import WorkspaceContextMixin
from tasks.models import Task, TaskList, Tag
from time_tracking.models import TimeEntry, TimeEntryTag

logger = logging.getLogger(__name__)


class TimeEntryListHTMLView(LoginRequiredMixin, WorkspaceContextMixin, View):
    """
    Time entry list page with comprehensive filtering.

    GET /time/entries/
    Query params: range, start_date, end_date, project_id, task_id, tags, billable

    Displays time entries with filters, daily subtotals, and grand total.
    """

    def get(self, request):
        """Handle GET request for time entry list page."""
        try:
            # Get workspace context from mixin
            workspace_context = self.get_workspace_context(request)
            current_workspace = workspace_context.get('current_workspace')

            # Get filter parameters
            range_filter = request.GET.get('range', 'current_week')
            start_date_str = request.GET.get('start_date')
            end_date_str = request.GET.get('end_date')
            task_id = request.GET.get('task_id')
            tags_str = request.GET.get('tags')  # Comma-separated tag IDs
            billable_filter = request.GET.get('billable')  # 'true', 'false', or None (all)

            # Calculate date range based on quick filter or custom dates
            if start_date_str and end_date_str:
                # Custom date range
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    range_filter = 'custom'
                except ValueError:
                    # Invalid date format, fall back to current week
                    start_date, end_date = self._get_current_week_range()
                    range_filter = 'current_week'
            else:
                # Quick filter
                if range_filter == 'last_7_days':
                    start_date, end_date = self._get_last_n_days_range(7)
                elif range_filter == 'last_30_days':
                    start_date, end_date = self._get_last_n_days_range(30)
                else:  # Default: current_week
                    start_date, end_date = self._get_current_week_range()
                    range_filter = 'current_week'

            # Build base queryset with permission check
            queryset = TimeEntry.objects.filter(
                user=request.user,
                is_running=False  # Exclude running timers
            ).select_related(
                'task',
                'project',
                'user'
            ).prefetch_related(
                Prefetch(
                    'time_entry_tags',
                    queryset=TimeEntryTag.objects.select_related('tag')
                )
            )

            # Apply date range filter
            # Filter by start_time if available, otherwise use created_at
            queryset = queryset.filter(
                Q(start_time__date__gte=start_date, start_time__date__lte=end_date) |
                Q(start_time__isnull=True, created_at__date__gte=start_date, created_at__date__lte=end_date)
            )

            # Apply task filter
            if task_id:
                queryset = queryset.filter(task_id=task_id)

            # Apply tags filter (OR logic: entries with ANY of the selected tags)
            if tags_str:
                try:
                    tag_ids = [int(tid.strip()) for tid in tags_str.split(',') if tid.strip()]
                    if tag_ids:
                        queryset = queryset.filter(time_entry_tags__tag_id__in=tag_ids).distinct()
                except ValueError:
                    # Invalid tag IDs, ignore filter
                    pass

            # Apply billable filter
            if billable_filter == 'true':
                queryset = queryset.filter(is_billable=True)
            elif billable_filter == 'false':
                queryset = queryset.filter(is_billable=False)
            # If None or 'all', show all entries (no filter)

            # Order by date (newest first)
            queryset = queryset.order_by('-start_time', '-created_at')

            # Fetch entries
            entries = list(queryset)

            # Calculate daily subtotals
            daily_totals = self._calculate_daily_totals(entries)

            # Calculate grand total
            grand_total = sum(
                (entry.duration for entry in entries if entry.duration),
                timedelta(0)
            )

            # Calculate billable totals if applicable
            billable_total = timedelta(0)
            revenue_total = 0.0

            if billable_filter in [None, 'true']:  # Show billable stats for 'all' or 'billable only'
                for entry in entries:
                    if entry.is_billable and entry.duration:
                        billable_total += entry.duration
                        if entry.billable_rate:
                            hours = entry.duration.total_seconds() / 3600
                            revenue_total += float(hours * float(entry.billable_rate))

            # Get user's tasks for filter dropdown (all tasks for current workspace)
            if current_workspace:
                user_tasks = Task.objects.filter(
                    task_list__workspace=current_workspace
                ).select_related('task_list').order_by('title')
            else:
                user_tasks = Task.objects.none()

            # Get tags used in user's time entries
            user_tags = Tag.objects.filter(
                time_entry_tags__time_entry__user=request.user
            ).distinct().order_by('name')

            # Parse selected tags for template
            selected_tags = []
            if tags_str:
                try:
                    tag_ids = [int(tid.strip()) for tid in tags_str.split(',') if tid.strip()]
                    selected_tags = tag_ids
                except ValueError:
                    pass

            # Build filter context for URL persistence
            filters = {
                'range': range_filter,
                'start_date': start_date_str or '',
                'end_date': end_date_str or '',
                'task_id': task_id or '',
                'tags': tags_str or '',
                'billable': billable_filter or '',
            }

            context = {
                **workspace_context,  # Spread workspace context from mixin
                'entries': entries,
                'daily_totals': daily_totals,
                'grand_total': grand_total,
                'billable_total': billable_total,
                'revenue_total': revenue_total,
                'user_tasks': user_tasks,
                'user_tags': user_tags,
                'selected_tags': selected_tags,
                'filters': filters,
                'start_date': start_date,
                'end_date': end_date,
                'active_range': range_filter,
                'show_revenue': billable_filter in [None, 'true'],
            }

            return render(request, 'time_tracking/time_entry_list.html', context)

        except Exception as e:
            logger.error(f"Error rendering time entry list: {e}", exc_info=True)
            # Get workspace context from mixin for error page
            workspace_context = self.get_workspace_context(request)

            # Return error page or empty list
            context = {
                **workspace_context,  # Spread workspace context from mixin
                'entries': [],
                'daily_totals': [],
                'grand_total': timedelta(0),
                'error_message': 'An error occurred while loading time entries. Please try again.',
            }
            return render(request, 'time_tracking/time_entry_list.html', context)

    def _get_current_week_range(self):
        """
        Get start and end dates for current calendar week (Monday-Sunday).

        Returns:
            tuple: (start_date, end_date) as date objects
        """
        today = date.today()
        monday = today - timedelta(days=today.weekday())  # Monday of current week
        sunday = monday + timedelta(days=6)  # Sunday of current week
        return monday, sunday

    def _get_last_n_days_range(self, n):
        """
        Get start and end dates for last N days including today.

        Args:
            n: Number of days (e.g., 7 for last 7 days, 30 for last 30 days)

        Returns:
            tuple: (start_date, end_date) as date objects
        """
        today = date.today()
        start_date = today - timedelta(days=n - 1)  # Include today
        return start_date, today

    def _calculate_daily_totals(self, entries):
        """
        Calculate total duration per day.

        Args:
            entries: List of TimeEntry objects

        Returns:
            list: List of tuples (date, total_duration)
        """
        daily_totals = []

        # Group entries by date
        def get_entry_date(entry):
            if entry.start_time:
                return entry.start_time.date()
            return entry.created_at.date()

        # Sort entries by date
        sorted_entries = sorted(entries, key=get_entry_date, reverse=True)

        # Group by date and calculate totals
        for entry_date, group in groupby(sorted_entries, key=get_entry_date):
            group_list = list(group)
            total = sum(
                (entry.duration for entry in group_list if entry.duration),
                timedelta(0)
            )
            daily_totals.append((entry_date, total))

        return daily_totals
