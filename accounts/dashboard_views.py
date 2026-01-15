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
    Main dashboard view with sidebar navigation.
    Supports workspace and task list selection via URL parameters.
    Optimized queries to avoid N+1 issues (5-6 queries total).
    """
    user = request.user

    # Query 1: Get all workspaces
    workspaces = user.workspaces.all()

    # Query 2: Get current workspace (0-1 queries depending on cache)
    workspace_id = request.GET.get('workspace')
    if workspace_id:
        current_workspace = get_object_or_404(Workspace, id=workspace_id, owner=user)
    elif workspaces.exists():
        current_workspace = workspaces.first()
    else:
        current_workspace = None

    # Handle no workspace case
    if not current_workspace:
        context = {
            'user': user,
            'workspaces': workspaces,
            'current_workspace': None,
        }
        return render(request, 'dashboard/home.html', context)

    # Query 3: Get task lists with counts (single query with annotations)
    task_lists = TaskList.objects.filter(
        workspace=current_workspace
    ).annotate(
        active_count=Count('tasks', filter=Q(tasks__status='active')),
        completed_count=Count('tasks', filter=Q(tasks__status='completed'))
    ).order_by('-created_at')

    # Get selected task list
    tasklist_id = request.GET.get('tasklist')
    selected_tasklist = None
    tasks = []

    if tasklist_id:
        # User selected specific task list (0-1 queries)
        selected_tasklist = get_object_or_404(
            TaskList,
            id=tasklist_id,
            workspace=current_workspace
        )
    elif task_lists.exists():
        # Auto-select first task list (0 queries - from queryset)
        selected_tasklist = task_lists.first()

    # Query 4: Fetch tasks with related data if task list selected
    if selected_tasklist:
        tasks = Task.objects.filter(
            task_list=selected_tasklist
        ).select_related(
            'created_by',
            'task_list',
            'task_list__workspace'
        ).prefetch_related(
            'tags'
        ).order_by('-created_at')

    # Query 5: Workspace-level stats (single aggregation query)
    workspace_stats = Task.objects.filter(
        task_list__workspace=current_workspace
    ).aggregate(
        active_count=Count('id', filter=Q(status='active')),
        completed_count=Count('id', filter=Q(status='completed'))
    )

    # Query 6: Recent tasks for overview mode (limit 10, optimized)
    recent_tasks = Task.objects.filter(
        task_list__workspace=current_workspace
    ).select_related(
        'task_list',
        'created_by'
    ).prefetch_related(
        'tags'
    ).order_by('-created_at')[:10]

    context = {
        'user': user,
        'workspaces': workspaces,
        'current_workspace': current_workspace,
        'task_lists': task_lists,
        'selected_tasklist': selected_tasklist,
        'tasks': tasks,
        'active_tasks': workspace_stats['active_count'],
        'completed_tasks': workspace_stats['completed_count'],
        'recent_tasks': recent_tasks,
    }

    return render(request, 'dashboard/home.html', context)
