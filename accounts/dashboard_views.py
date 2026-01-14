"""
Dashboard views for authenticated users.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from tasks.models import Task, TaskList
from accounts.models import Workspace


@login_required
def dashboard_view(request):
    """
    Main dashboard view for authenticated users.
    Displays recent tasks and task lists from user's workspaces.
    """
    user = request.user

    # Get user's workspaces
    workspaces = user.workspaces.all()

    # Get current workspace (from query param or default to first)
    workspace_id = request.GET.get('workspace')
    if workspace_id:
        current_workspace = get_object_or_404(Workspace, id=workspace_id, owner=user)
    elif workspaces.exists():
        current_workspace = workspaces.first()
    else:
        current_workspace = None

    if current_workspace:
        # Get task lists for current workspace with task counts
        task_lists = TaskList.objects.filter(
            workspace=current_workspace
        ).annotate(
            active_count=Count('tasks', filter=Q(tasks__status='active')),
            completed_count=Count('tasks', filter=Q(tasks__status='completed'))
        ).order_by('-created_at')[:5]

        # Get recent tasks across all task lists in current workspace
        recent_tasks = Task.objects.filter(
            task_list__workspace=current_workspace
        ).select_related('task_list', 'created_by').order_by('-created_at')[:10]

        # Get task counts for current workspace
        active_tasks = Task.objects.filter(
            task_list__workspace=current_workspace,
            status='active'
        ).count()

        completed_tasks = Task.objects.filter(
            task_list__workspace=current_workspace,
            status='completed'
        ).count()

        context = {
            'user': user,
            'workspaces': workspaces,
            'current_workspace': current_workspace,
            'task_lists': task_lists,
            'recent_tasks': recent_tasks,
            'active_tasks': active_tasks,
            'completed_tasks': completed_tasks,
        }

        return render(request, 'dashboard/home.html', context)
    else:
        # No workspaces - this shouldn't happen with signal-created workspaces
        # but handle gracefully
        context = {
            'user': user,
            'workspaces': workspaces,
        }
        return render(request, 'dashboard/home.html', context)
