"""
Mixins for providing workspace context to views.

This module contains reusable mixins that provide consistent workspace and task list
context across all views in the application.
"""
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q

from accounts.models import Workspace
from tasks.models import TaskList


class WorkspaceContextMixin:
    """
    Mixin to provide consistent workspace and task list context to all views.

    This mixin centralizes the logic for retrieving and providing workspace-related
    context variables that are needed by templates, particularly the dashboard sidebar.

    Context Variables Added:
        workspaces (QuerySet): All workspaces owned by the current user
        current_workspace (Workspace|None): Currently selected workspace (from URL param or first workspace)
        task_lists (QuerySet): Task lists for current workspace with active/completed count annotations
        selected_tasklist (TaskList|None): Currently selected task list from URL param (optional)

    URL Parameters:
        workspace (int): Workspace ID to select (optional, defaults to first workspace)
        tasklist (int): Task list ID to select (optional)

    Usage Example:
        class MyView(LoginRequiredMixin, WorkspaceContextMixin, TemplateView):
            template_name = 'my_template.html'

            # Workspace context automatically available in template
            # No need to manually add workspaces, current_workspace, etc.

    Notes:
        - Uses optimized queries with annotations to prevent N+1 problems
        - Validates workspace ownership via get_object_or_404
        - Handles edge cases gracefully (no workspaces, no task lists, invalid IDs)
        - Consistent with dashboard view's query patterns
        - Task lists include active_count and completed_count annotations
    """

    def get_workspace_context(self, request):
        """
        Build workspace context dictionary with optimized queries.

        Args:
            request (HttpRequest): Django request object

        Returns:
            dict: Dictionary containing workspaces, current_workspace, task_lists, selected_tasklist

        Query Optimization:
            - Total queries: 2-4 depending on URL parameters
            - Query 1: Get all user's workspaces
            - Query 2: Get current workspace (conditional, only if workspace param provided)
            - Query 3: Get task lists with annotated counts (single query with Count aggregations)
            - Query 4: Get selected task list (conditional, only if tasklist param provided)
        """
        # Query 1: Get all user's workspaces
        workspaces = request.user.workspaces.all()

        # Query 2: Get current workspace (from URL param or first workspace)
        workspace_id = request.GET.get('workspace')

        if workspace_id:
            # User specified workspace ID in URL - validate ownership
            current_workspace = get_object_or_404(
                Workspace,
                id=workspace_id,
                owner=request.user
            )
        elif workspaces.exists():
            # No workspace param - default to first workspace
            current_workspace = workspaces.first()
        else:
            # User has no workspaces
            current_workspace = None

        # Query 3: Get task lists with annotations for counts (single optimized query)
        if current_workspace:
            task_lists = TaskList.objects.filter(
                workspace=current_workspace
            ).annotate(
                # Count active tasks (not archived)
                active_count=Count(
                    'tasks',
                    filter=Q(tasks__status='active', tasks__is_archived=False)
                ),
                # Count completed tasks (not archived)
                completed_count=Count(
                    'tasks',
                    filter=Q(tasks__status='completed', tasks__is_archived=False)
                )
            ).order_by('-created_at')
        else:
            # No workspace selected - return empty queryset (safe for templates)
            task_lists = TaskList.objects.none()

        # Query 4: Get selected task list (optional, from URL param)
        tasklist_id = request.GET.get('tasklist')
        selected_tasklist = None

        if tasklist_id and current_workspace:
            try:
                # Try to get task list from already-fetched task_lists queryset
                selected_tasklist = task_lists.get(id=tasklist_id)
            except TaskList.DoesNotExist:
                # Invalid tasklist ID or doesn't belong to current workspace
                # Gracefully ignore - don't crash, just don't select any list
                selected_tasklist = None

        return {
            'workspaces': workspaces,
            'current_workspace': current_workspace,
            'task_lists': task_lists,
            'selected_tasklist': selected_tasklist,
        }

    def get_context_data(self, **kwargs):
        """
        Add workspace context to existing context.

        This method is called automatically by Django's class-based views.
        It merges the workspace context with any other context provided by the view.

        Args:
            **kwargs: Existing context data from parent classes

        Returns:
            dict: Merged context dictionary with workspace context added
        """
        context = super().get_context_data(**kwargs)
        workspace_context = self.get_workspace_context(self.request)
        context.update(workspace_context)
        return context
