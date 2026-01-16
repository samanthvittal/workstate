"""
Views module for tasks app.

Exports all view classes for use in URL configuration.
"""
from tasks.views.task_views import (
    TaskCreateView,
    TaskUpdateView,
    TaskListView,
    TaskDetailView,
    TaskQuickDateView,
    TaskToggleStatusView,
    TaskListCreateView,
    TaskListListView,
    TaskListDetailView,
    TaskListMarkAllCompleteView,
    TaskArchiveView,
    TaskUnarchiveView,
    TaskListArchiveAllCompletedView,
    ArchivedTaskListView,
    WorkspaceAccessMixin,
    TaskListAccessMixin,
)

from tasks.views.search_views import (
    SearchDropdownView,
    SearchResultsView,
    SaveSearchView,
    DeleteSearchView,
    ClearSearchHistoryView,
)

__all__ = [
    # Task views
    'TaskCreateView',
    'TaskUpdateView',
    'TaskListView',
    'TaskDetailView',
    'TaskQuickDateView',
    'TaskToggleStatusView',
    # Task list views
    'TaskListCreateView',
    'TaskListListView',
    'TaskListDetailView',
    # Bulk actions and archive views
    'TaskListMarkAllCompleteView',
    'TaskArchiveView',
    'TaskUnarchiveView',
    'TaskListArchiveAllCompletedView',
    'ArchivedTaskListView',
    # Mixins
    'WorkspaceAccessMixin',
    'TaskListAccessMixin',
    # Search views
    'SearchDropdownView',
    'SearchResultsView',
    'SaveSearchView',
    'DeleteSearchView',
    'ClearSearchHistoryView',
]
