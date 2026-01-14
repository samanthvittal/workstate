"""
Views for task and task list creation, editing, listing, and detail display.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, ListView, DetailView

from accounts.models import Workspace
from tasks.forms import TaskForm, TaskListForm
from tasks.models import Task, TaskList


class WorkspaceAccessMixin:
    """
    Mixin to verify user owns workspace from URL parameter.
    Raises PermissionDenied if user is not workspace owner.
    """

    def dispatch(self, request, *args, **kwargs):
        """Check workspace access before dispatching request."""
        workspace_id = kwargs.get('workspace_id')
        if workspace_id:
            workspace = get_object_or_404(Workspace, id=workspace_id)
            if workspace.owner != request.user:
                raise PermissionDenied("You do not have access to this workspace.")
            # Store workspace for use in view methods
            self.workspace = workspace
        return super().dispatch(request, *args, **kwargs)


class TaskListAccessMixin:
    """
    Mixin to verify user owns task list (via workspace ownership) from URL parameter.
    Raises PermissionDenied if user is not workspace owner.
    """

    def dispatch(self, request, *args, **kwargs):
        """Check task list access before dispatching request."""
        tasklist_id = kwargs.get('tasklist_id')
        if tasklist_id:
            task_list = get_object_or_404(TaskList, id=tasklist_id)
            if task_list.workspace.owner != request.user:
                raise PermissionDenied("You do not have access to this task list.")
            # Store task_list and workspace for use in view methods
            self.task_list = task_list
            self.workspace = task_list.workspace
        return super().dispatch(request, *args, **kwargs)


# ============================================================================
# Task List Views
# ============================================================================

class TaskListCreateView(LoginRequiredMixin, WorkspaceAccessMixin, CreateView):
    """
    View for creating a new task list within a workspace.
    Requires authentication and workspace access.
    """
    model = TaskList
    form_class = TaskListForm
    template_name = 'tasks/tasklist_form.html'

    def get_success_url(self):
        """Redirect to workspace task lists after creation."""
        return reverse('tasks:tasklist-list', kwargs={'workspace_id': self.workspace.id})

    def form_valid(self, form):
        """Set workspace and created_by before saving task list."""
        form.instance.workspace = self.workspace
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Task list "{form.instance.name}" created successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Add workspace and form action URL to context."""
        context = super().get_context_data(**kwargs)
        context['workspace'] = self.workspace
        context['form_action'] = self.request.path
        context['cancel_url'] = reverse('tasks:tasklist-list', kwargs={'workspace_id': self.workspace.id})
        return context


class TaskListListView(LoginRequiredMixin, WorkspaceAccessMixin, ListView):
    """
    View for displaying all task lists in a workspace with their tasks.
    """
    model = TaskList
    template_name = 'tasks/tasklist_list.html'
    context_object_name = 'task_lists'

    def get_queryset(self):
        """Get task lists for the workspace with task counts."""
        return TaskList.objects.filter(
            workspace=self.workspace
        ).prefetch_related('tasks').select_related('workspace', 'created_by').order_by('-created_at')

    def get_context_data(self, **kwargs):
        """Add workspace and counts to context."""
        context = super().get_context_data(**kwargs)
        context['workspace'] = self.workspace

        # Get task counts for each list
        for task_list in context['task_lists']:
            task_list.active_count = task_list.tasks.filter(status='active').count()
            task_list.completed_count = task_list.tasks.filter(status='completed').count()

        return context


class TaskListDetailView(LoginRequiredMixin, DetailView):
    """
    View for displaying a single task list with all its tasks.
    """
    model = TaskList
    template_name = 'tasks/tasklist_detail.html'
    context_object_name = 'task_list'
    pk_url_kwarg = 'tasklist_id'

    def get_queryset(self):
        """Filter task lists to only those in workspaces owned by the user."""
        return TaskList.objects.filter(
            workspace__owner=self.request.user
        ).prefetch_related('tasks').select_related('workspace', 'created_by')

    def get_context_data(self, **kwargs):
        """Add workspace and tasks to context."""
        context = super().get_context_data(**kwargs)
        context['workspace'] = self.object.workspace
        context['tasks'] = self.object.tasks.all().select_related('created_by').order_by('-created_at')
        context['active_count'] = self.object.tasks.filter(status='active').count()
        context['completed_count'] = self.object.tasks.filter(status='completed').count()
        return context


# ============================================================================
# Task Views
# ============================================================================

class TaskCreateView(LoginRequiredMixin, TaskListAccessMixin, CreateView):
    """
    View for creating a new task within a task list.
    Requires authentication and task list access (via workspace ownership).
    """
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

    def get_success_url(self):
        """Redirect to the same form URL after successful creation."""
        return self.request.path

    def form_valid(self, form):
        """Set task_list and created_by before saving task."""
        form.instance.task_list = self.task_list
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Task created successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Add task_list, workspace and form action URL to context."""
        context = super().get_context_data(**kwargs)
        context['task_list'] = self.task_list
        context['workspace'] = self.workspace
        context['form_action'] = self.request.path
        context['cancel_url'] = reverse('tasks:tasklist-detail', kwargs={'tasklist_id': self.task_list.id})
        return context


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for editing an existing task.
    Requires authentication and verifies task ownership via task_list's workspace.
    """
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_edit_form.html'

    def get_queryset(self):
        """Filter tasks to only those in workspaces owned by the user."""
        return Task.objects.filter(
            task_list__workspace__owner=self.request.user
        ).select_related('task_list__workspace', 'created_by')

    def get_success_url(self):
        """Redirect to task list detail."""
        return reverse('tasks:tasklist-detail', kwargs={'tasklist_id': self.object.task_list.id})

    def form_valid(self, form):
        """
        Handle status checkbox and add success message when task is updated.
        The checkbox sends 'completed' value when checked, nothing when unchecked.
        """
        # Handle status checkbox - if 'status' is in POST data with value 'completed', set it
        # Otherwise, set to 'active'
        if self.request.POST.get('status') == 'completed':
            form.instance.status = 'completed'
        else:
            form.instance.status = 'active'

        messages.success(self.request, 'Task updated successfully!')
        response = super().form_valid(form)

        # For HTMX requests, add HX-Trigger header to close modal
        if self.request.headers.get('HX-Request'):
            response['HX-Trigger'] = 'taskUpdated'

        return response

    def get_template_names(self):
        """Return partial template for HTMX requests."""
        if self.request.headers.get('HX-Request'):
            return ['tasks/task_edit_form.html']
        return ['tasks/task_edit_form.html']

    def get_context_data(self, **kwargs):
        """Add task and form action URL to context."""
        context = super().get_context_data(**kwargs)
        context['task'] = self.object
        context['task_list'] = self.object.task_list
        context['workspace'] = self.object.workspace
        context['form_action'] = reverse('tasks:task-edit', kwargs={'pk': self.object.pk})
        context['cancel_url'] = reverse('tasks:tasklist-detail', kwargs={'tasklist_id': self.object.task_list.id})
        return context


class TaskListView(LoginRequiredMixin, ListView):
    """
    View for displaying all tasks across all workspaces for a user.
    Can be filtered by workspace via query parameter.
    """
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 50

    def get_queryset(self):
        """Get tasks for the user, optionally filtered by workspace."""
        queryset = Task.objects.filter(
            task_list__workspace__owner=self.request.user
        ).select_related('task_list__workspace', 'created_by', 'task_list').order_by('-created_at')

        # Filter by workspace if specified in query params
        workspace_id = self.request.GET.get('workspace')
        if workspace_id:
            queryset = queryset.filter(task_list__workspace_id=workspace_id)

        return queryset

    def get_context_data(self, **kwargs):
        """Add workspace filter and counts to context."""
        context = super().get_context_data(**kwargs)

        # Get current workspace filter
        workspace_id = self.request.GET.get('workspace')
        if workspace_id:
            context['current_workspace'] = get_object_or_404(Workspace, id=workspace_id, owner=self.request.user)

            # Counts for current workspace
            context['active_count'] = Task.objects.filter(
                task_list__workspace=context['current_workspace'],
                status='active'
            ).count()
            context['completed_count'] = Task.objects.filter(
                task_list__workspace=context['current_workspace'],
                status='completed'
            ).count()
        else:
            # Counts for all workspaces
            context['active_count'] = Task.objects.filter(
                task_list__workspace__owner=self.request.user,
                status='active'
            ).count()
            context['completed_count'] = Task.objects.filter(
                task_list__workspace__owner=self.request.user,
                status='completed'
            ).count()

        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    """
    View for displaying a single task with all details.
    Verifies task ownership via task_list's workspace.
    """
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        """Filter tasks to only those in workspaces owned by the user."""
        return Task.objects.filter(
            task_list__workspace__owner=self.request.user
        ).select_related('task_list__workspace', 'created_by', 'task_list')

    def get_context_data(self, **kwargs):
        """Add workspace and task_list to context."""
        context = super().get_context_data(**kwargs)
        context['workspace'] = self.object.workspace
        context['task_list'] = self.object.task_list
        return context
