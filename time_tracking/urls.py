"""
URL configuration for time tracking app.
"""
from django.urls import path
from time_tracking.views.timer_views import (
    TimerStartView,
    TimerStopView,
    TimerDiscardView,
    TimerGetActiveView,
)
from time_tracking.views.time_entry_views import (
    TimeEntryListView,
    TimeEntryRetrieveView,
    TimeEntryCreateView,
    TimeEntryUpdateView,
    TimeEntryDeleteView,
)
from time_tracking.views.time_entry_list_views import TimeEntryListHTMLView
from time_tracking.views.time_entry_form_views import (
    TimeEntryCreateFormView,
    TimeEntryEditFormView,
    TimeEntryInlineEditView,
)
from time_tracking.views.idle_views import (
    IdleKeepView,
    IdleDiscardView,
    IdleStopView,
    IdleNotificationListView,
)
from time_tracking.views.pomodoro_views import (
    PomodoroStartView,
    PomodoroCompleteView,
    PomodoroBreakTakenView,
    PomodoroStatusView,
)
from time_tracking.views.goal_views import (
    TimeGoalListView,
    TimeGoalProgressAPIView,
    TimeGoalCreateAPIView,
    TimeGoalUpdateAPIView,
    TimeGoalDeleteAPIView,
)
from time_tracking.views.suggestion_views import TimeSuggestionAPIView
from time_tracking.views.analytics_views import AnalyticsDashboardView
from time_tracking.views.export_views import (
    ExportCSVView,
    ExportPDFView,
    ExportExcelView,
)
from time_tracking.views.settings_views import TimeTrackingSettingsView

app_name = 'time_tracking'

urlpatterns = [
    # Timer API endpoints
    path('api/timers/start/', TimerStartView.as_view(), name='timer-start'),
    path('api/timers/stop/', TimerStopView.as_view(), name='timer-stop'),
    path('api/timers/discard/', TimerDiscardView.as_view(), name='timer-discard'),
    path('api/timers/active/', TimerGetActiveView.as_view(), name='timer-get-active'),

    # Idle time action endpoints
    path('api/timers/idle/keep/', IdleKeepView.as_view(), name='idle-keep'),
    path('api/timers/idle/discard/', IdleDiscardView.as_view(), name='idle-discard'),
    path('api/timers/idle/stop/', IdleStopView.as_view(), name='idle-stop'),
    path('api/timers/idle/notifications/', IdleNotificationListView.as_view(), name='idle-notifications'),

    # Pomodoro endpoints
    path('api/pomodoro/start/', PomodoroStartView.as_view(), name='pomodoro-start'),
    path('api/pomodoro/<int:session_id>/complete/', PomodoroCompleteView.as_view(), name='pomodoro-complete'),
    path('api/pomodoro/<int:session_id>/break/', PomodoroBreakTakenView.as_view(), name='pomodoro-break'),
    path('api/pomodoro/status/', PomodoroStatusView.as_view(), name='pomodoro-status'),

    # Time goal endpoints
    path('goals/', TimeGoalListView.as_view(), name='goal-list'),
    path('api/goals/create/', TimeGoalCreateAPIView.as_view(), name='goal-create'),
    path('api/goals/<int:goal_id>/', TimeGoalProgressAPIView.as_view(), name='goal-progress'),
    path('api/goals/<int:goal_id>/update/', TimeGoalUpdateAPIView.as_view(), name='goal-update'),
    path('api/goals/<int:goal_id>/delete/', TimeGoalDeleteAPIView.as_view(), name='goal-delete'),

    # Time suggestion endpoint
    path('api/suggestions/<int:task_id>/', TimeSuggestionAPIView.as_view(), name='suggestion-get'),

    # Time Entry CRUD API endpoints
    # List (GET) and Create (POST) use same path with different HTTP methods
    path('api/time-entries/', TimeEntryListView.as_view(), name='time-entry-list'),
    path('api/time-entries/create/', TimeEntryCreateView.as_view(), name='time-entry-create'),

    # Retrieve (GET), Update (PATCH), Delete (DELETE) use same path with different HTTP methods
    path('api/time-entries/<int:entry_id>/', TimeEntryRetrieveView.as_view(), name='time-entry-retrieve'),
    path('api/time-entries/<int:entry_id>/update/', TimeEntryUpdateView.as_view(), name='time-entry-update'),
    path('api/time-entries/<int:entry_id>/delete/', TimeEntryDeleteView.as_view(), name='time-entry-delete'),

    # HTML Views
    path('entries/', TimeEntryListHTMLView.as_view(), name='time-entry-list-html'),
    path('entries/new/', TimeEntryCreateFormView.as_view(), name='time-entry-create-form'),
    path('entries/<int:entry_id>/edit/', TimeEntryEditFormView.as_view(), name='time-entry-edit'),
    path('entries/<int:entry_id>/inline-edit/', TimeEntryInlineEditView.as_view(), name='time-entry-inline-edit'),

    # Analytics and Reporting
    path('analytics/', AnalyticsDashboardView.as_view(), name='analytics-dashboard'),

    # Export endpoints
    path('export/csv/', ExportCSVView.as_view(), name='export-csv'),
    path('export/pdf/', ExportPDFView.as_view(), name='export-pdf'),
    path('export/excel/', ExportExcelView.as_view(), name='export-excel'),

    # Settings
    path('settings/', TimeTrackingSettingsView.as_view(), name='settings'),
]
