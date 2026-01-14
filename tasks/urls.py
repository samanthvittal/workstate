"""
URL configuration for tasks app.
"""
from django.urls import path
from tasks.views import (
    TaskCreateView, TaskUpdateView, TaskListView, TaskDetailView,
    TaskListCreateView, TaskListListView, TaskListDetailView
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

    # All tasks view (can be filtered by workspace via query param)
    path('tasks/', TaskListView.as_view(), name='task-list-all'),
]
