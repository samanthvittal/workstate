"""
URL configuration for tasks app.
"""
from django.urls import path
from tasks.views import (
    TaskCreateView, TaskUpdateView, TaskListView, TaskDetailView, TaskQuickDateView,
    TaskToggleStatusView,
    TaskListCreateView, TaskListListView, TaskListDetailView,
    TaskListMarkAllCompleteView, TaskArchiveView, TaskUnarchiveView, TaskListArchiveAllCompletedView,
    ArchivedTaskListView
)

app_name = 'tasks'

urlpatterns = [
    # Task List URLs
    path('workspace/<int:workspace_id>/tasklists/', TaskListListView.as_view(), name='tasklist-list'),
    path('workspace/<int:workspace_id>/tasklists/create/', TaskListCreateView.as_view(), name='tasklist-create'),
    path('tasklist/<int:tasklist_id>/', TaskListDetailView.as_view(), name='tasklist-detail'),

    # Task URLs
    path('tasklist/<int:tasklist_id>/tasks/create/', TaskCreateView.as_view(), name='task-create'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('tasks/<int:pk>/edit/', TaskUpdateView.as_view(), name='task-edit'),
    path('tasks/<int:pk>/quick-date/', TaskQuickDateView.as_view(), name='task-quick-date'),
    path('tasks/<int:pk>/toggle-status/', TaskToggleStatusView.as_view(), name='toggle-status'),

    # Bulk Actions & Archive URLs
    path('tasklist/<int:pk>/mark-all-complete/', TaskListMarkAllCompleteView.as_view(), name='mark-all-complete'),
    path('tasks/<int:pk>/archive/', TaskArchiveView.as_view(), name='archive-task'),
    path('tasks/<int:pk>/unarchive/', TaskUnarchiveView.as_view(), name='unarchive-task'),
    path('tasklist/<int:pk>/archive-all-completed/', TaskListArchiveAllCompletedView.as_view(), name='archive-all-completed'),
    path('tasks/archived/', ArchivedTaskListView.as_view(), name='archived-tasks'),

    # All tasks view (can be filtered by workspace via query param)
    path('tasks/', TaskListView.as_view(), name='task-list-all'),
]
