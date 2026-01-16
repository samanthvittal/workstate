"""
Analytics dashboard views for time tracking reports and statistics.

Provides comprehensive analytics dashboard with summary statistics, charts,
and breakdowns by project, task, and tag.
"""
import logging
import json
from datetime import datetime, timedelta, date
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from accounts.mixins import WorkspaceContextMixin
from time_tracking.services.analytics import AnalyticsService

logger = logging.getLogger(__name__)


class AnalyticsDashboardView(LoginRequiredMixin, WorkspaceContextMixin, View):
    """
    Analytics dashboard page with summary statistics and charts.

    GET /time/analytics/
    Query params: range, start_date, end_date

    Displays summary statistics, project/task/tag breakdowns, time-of-day heatmap,
    and day-of-week patterns.
    """

    def get(self, request):
        """Handle GET request for analytics dashboard."""
        try:
            # Get workspace context from mixin
            workspace_context = self.get_workspace_context(request)

            # Get filter parameters
            range_filter = request.GET.get('range', 'this_month')
            start_date_str = request.GET.get('start_date')
            end_date_str = request.GET.get('end_date')

            # Calculate date range based on quick filter or custom dates
            if start_date_str and end_date_str:
                # Custom date range
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    range_filter = 'custom'
                except ValueError:
                    # Invalid date format, fall back to this month
                    start_date, end_date = self._get_this_month_range()
                    range_filter = 'this_month'
            else:
                # Quick filter
                if range_filter == 'today':
                    start_date, end_date = self._get_today_range()
                elif range_filter == 'this_week':
                    start_date, end_date = self._get_this_week_range()
                elif range_filter == 'last_month':
                    start_date, end_date = self._get_last_month_range()
                elif range_filter == 'last_3_months':
                    start_date, end_date = self._get_last_n_months_range(3)
                elif range_filter == 'this_year':
                    start_date, end_date = self._get_this_year_range()
                else:  # Default: this_month
                    start_date, end_date = self._get_this_month_range()
                    range_filter = 'this_month'

            # Initialize analytics service
            analytics = AnalyticsService(request.user)

            # Calculate summary statistics
            summary = analytics.get_summary_statistics(start_date, end_date)

            # Calculate today's summary for comparison
            today = date.today()
            today_summary = analytics.get_summary_statistics(today, today)

            # Calculate this week's summary
            week_start, week_end = self._get_this_week_range()
            week_summary = analytics.get_summary_statistics(week_start, week_end)

            # Get breakdowns
            project_breakdown = analytics.get_project_breakdown(start_date, end_date)
            task_breakdown = analytics.get_task_breakdown(start_date, end_date, limit=10)
            tag_breakdown = analytics.get_tag_breakdown(start_date, end_date)

            # Get time patterns
            time_of_day_heatmap = analytics.get_time_of_day_heatmap(start_date, end_date)
            day_of_week_patterns = analytics.get_day_of_week_patterns(start_date, end_date)

            # Prepare chart data (convert to JSON for JavaScript)
            project_chart_data = self._prepare_project_chart_data(project_breakdown)
            task_chart_data = self._prepare_task_chart_data(task_breakdown)
            tag_chart_data = self._prepare_tag_chart_data(tag_breakdown)
            heatmap_chart_data = self._prepare_heatmap_chart_data(time_of_day_heatmap)
            day_pattern_chart_data = self._prepare_day_pattern_chart_data(day_of_week_patterns)

            context = {
                **workspace_context,  # Spread workspace context from mixin

                # Date range
                'start_date': start_date,
                'end_date': end_date,
                'active_range': range_filter,

                # Summary statistics
                'summary': summary,
                'today_summary': today_summary,
                'week_summary': week_summary,

                # Breakdowns
                'project_breakdown': project_breakdown,
                'task_breakdown': task_breakdown,
                'tag_breakdown': tag_breakdown,

                # Patterns
                'time_of_day_heatmap': time_of_day_heatmap,
                'day_of_week_patterns': day_of_week_patterns,

                # Chart data (JSON)
                'project_chart_data': json.dumps(project_chart_data),
                'task_chart_data': json.dumps(task_chart_data),
                'tag_chart_data': json.dumps(tag_chart_data),
                'heatmap_chart_data': json.dumps(heatmap_chart_data),
                'day_pattern_chart_data': json.dumps(day_pattern_chart_data),
            }

            return render(request, 'time_tracking/analytics_dashboard.html', context)

        except Exception as e:
            logger.error(f"Error rendering analytics dashboard: {e}", exc_info=True)
            # Get workspace context from mixin for error page
            workspace_context = self.get_workspace_context(request)

            context = {
                **workspace_context,  # Spread workspace context from mixin
                'error_message': 'An error occurred while loading analytics. Please try again.',
            }
            return render(request, 'time_tracking/analytics_dashboard.html', context)

    def _get_today_range(self):
        """Get start and end dates for today."""
        today = date.today()
        return today, today

    def _get_this_week_range(self):
        """Get start and end dates for current calendar week (Monday-Sunday)."""
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return monday, sunday

    def _get_this_month_range(self):
        """Get start and end dates for current month."""
        today = date.today()
        first_day = today.replace(day=1)
        # Get last day of month
        if today.month == 12:
            last_day = today.replace(day=31)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
            last_day = next_month - timedelta(days=1)
        return first_day, last_day

    def _get_last_month_range(self):
        """Get start and end dates for last month."""
        today = date.today()
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        return first_day_last_month, last_day_last_month

    def _get_last_n_months_range(self, n):
        """Get start and end dates for last N months."""
        today = date.today()
        end_date = today
        # Go back n months
        month = today.month - n
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        start_date = date(year, month, 1)
        return start_date, end_date

    def _get_this_year_range(self):
        """Get start and end dates for current year."""
        today = date.today()
        first_day = date(today.year, 1, 1)
        last_day = date(today.year, 12, 31)
        return first_day, last_day

    def _prepare_project_chart_data(self, project_breakdown):
        """Prepare project breakdown data for Chart.js pie chart."""
        return {
            'labels': [item['project_name'] for item in project_breakdown],
            'data': [item['total_duration'].total_seconds() / 3600 for item in project_breakdown],
            'counts': [item['entry_count'] for item in project_breakdown],
        }

    def _prepare_task_chart_data(self, task_breakdown):
        """Prepare task breakdown data for Chart.js horizontal bar chart."""
        return {
            'labels': [item['task_name'] for item in task_breakdown],
            'data': [item['total_duration'].total_seconds() / 3600 for item in task_breakdown],
            'projects': [item['project_name'] for item in task_breakdown],
        }

    def _prepare_tag_chart_data(self, tag_breakdown):
        """Prepare tag breakdown data for Chart.js bar chart."""
        return {
            'labels': [item['tag_name'] for item in tag_breakdown],
            'data': [item['total_duration'].total_seconds() / 3600 for item in tag_breakdown],
            'counts': [item['entry_count'] for item in tag_breakdown],
        }

    def _prepare_heatmap_chart_data(self, heatmap):
        """Prepare time-of-day heatmap data for Chart.js."""
        return {
            'labels': [f"{hour:02d}:00" for hour in range(24)],
            'data': [heatmap[hour].total_seconds() / 3600 for hour in range(24)],
        }

    def _prepare_day_pattern_chart_data(self, patterns):
        """Prepare day-of-week patterns data for Chart.js."""
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        return {
            'labels': day_names,
            'total_data': [patterns[day]['total_duration'].total_seconds() / 3600 for day in range(7)],
            'billable_data': [patterns[day]['billable_duration'].total_seconds() / 3600 for day in range(7)],
            'non_billable_data': [patterns[day]['non_billable_duration'].total_seconds() / 3600 for day in range(7)],
        }
