"""
Views for task and task list creation, editing, listing, and detail display.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Case, When, Value, IntegerField, Q, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from datetime import date, timedelta

from accounts.models import Workspace, UserPreference
from accounts.mixins import WorkspaceContextMixin
from tasks.forms import TaskForm, TaskListForm
from tasks.models import Task, TaskList, Tag


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
        """Redirect to dashboard with new task list selected."""
        return f'/dashboard/?workspace={self.workspace.id}&tasklist={self.object.id}'

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


class TaskListDetailView(LoginRequiredMixin, WorkspaceContextMixin, DetailView):
    """
    View for displaying a single task list with all its tasks.
    Includes workspace context for sidebar navigation.
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
        """Add workspace context from mixin and task list specific data."""
        # WorkspaceContextMixin automatically adds workspace context via super()
        context = super().get_context_data(**kwargs)

        # Add task list specific context
        context['workspace'] = self.object.workspace
        context['tasks'] = self.object.tasks.filter(is_archived=False).select_related('created_by').prefetch_related('tags').annotate(
            sort_order=Case(
                When(status='completed', then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('sort_order', '-created_at')
        context['active_count'] = self.object.tasks.filter(status='active', is_archived=False).count()
        context['completed_count'] = self.object.tasks.filter(status='completed', is_archived=False).count()
        context['total_count'] = context['active_count'] + context['completed_count']
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
        """Set task_list and created_by before saving task, then handle tags."""
        form.instance.task_list = self.task_list
        form.instance.created_by = self.request.user

        # Save the task first (required before adding many-to-many relationships)
        response = super().form_valid(form)

        # Handle tag creation and association
        tag_names = form.cleaned_data.get('tags_input', [])
        if tag_names:
            # Create or get tags for this workspace
            tags = []
            for tag_name in tag_names:
                tag = Tag.objects.get_or_create_tag(
                    name=tag_name,
                    workspace=self.workspace,
                    user=self.request.user
                )
                if tag:  # get_or_create_tag returns None for empty names
                    tags.append(tag)

            # Associate tags with task
            form.instance.tags.set(tags)

            # Success message with tag count
            tag_count = len(tags)
            if tag_count == 1:
                messages.success(self.request, f'Task created successfully with 1 tag!')
            else:
                messages.success(self.request, f'Task created successfully with {tag_count} tags!')
        else:
            messages.success(self.request, 'Task created successfully!')

        return response

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
    template_name = 'tasks/task_edit.html'

    def get_queryset(self):
        """Filter tasks to only those in workspaces owned by the user."""
        return Task.objects.filter(
            task_list__workspace__owner=self.request.user
        ).select_related('task_list__workspace', 'created_by')

    def get_success_url(self):
        """Redirect to task detail page."""
        return reverse('tasks:task-detail', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        """Add task list and workspace to context."""
        context = super().get_context_data(**kwargs)
        context['task'] = self.object
        context['task_list'] = self.object.task_list
        context['workspace'] = self.object.task_list.workspace
        context['form_action'] = reverse('tasks:task-edit', kwargs={'pk': self.object.id})

        # Add sidebar counts (required by task_sidebar.html)
        from django.db.models import Q, Count
        from django.utils import timezone

        workspace = self.object.task_list.workspace
        today = timezone.now().date()

        # Get task counts for sidebar
        tasks = Task.objects.filter(
            task_list__workspace=workspace,
            is_archived=False
        )

        context['total_count'] = tasks.count()
        context['active_count'] = tasks.filter(status='active').count()
        context['completed_count'] = tasks.filter(status='completed').count()

        # Due date counts
        context['today_count'] = tasks.filter(due_date=today).count()
        context['today_completed_count'] = tasks.filter(due_date=today, status='completed').count()

        context['upcoming_count'] = tasks.filter(due_date__gt=today).count()
        context['upcoming_completed_count'] = tasks.filter(due_date__gt=today, status='completed').count()

        context['overdue_count'] = tasks.filter(due_date__lt=today, status='active').count()
        context['overdue_completed_count'] = 0

        context['archived_count'] = Task.objects.filter(
            task_list__workspace=workspace,
            is_archived=True
        ).count()

        return context

    def form_valid(self, form):
        """
        Handle status checkbox, tags, and add success message when task is updated.
        The checkbox sends 'completed' value when checked, nothing when unchecked.
        """
        # Handle status checkbox - if 'status' is in POST data with value 'completed', set it
        # Otherwise, set to 'active'
        if self.request.POST.get('status') == 'completed':
            form.instance.status = 'completed'
        else:
            form.instance.status = 'active'

        # Save the task first (required before modifying many-to-many relationships)
        response = super().form_valid(form)

        # Handle tag updates - clear existing and reassign
        tag_names = form.cleaned_data.get('tags_input', [])
        workspace = self.object.task_list.workspace

        # Clear existing tags
        form.instance.tags.clear()

        # Add new tags
        if tag_names:
            tags = []
            for tag_name in tag_names:
                tag = Tag.objects.get_or_create_tag(
                    name=tag_name,
                    workspace=workspace,
                    user=self.request.user
                )
                if tag:  # get_or_create_tag returns None for empty names
                    tags.append(tag)

            # Associate tags with task
            form.instance.tags.set(tags)

        messages.success(self.request, 'Task updated successfully!')

        return response


class TaskToggleStatusView(LoginRequiredMixin, View):
    """
    View for toggling task completion status via HTMX.
    Handles POST request to flip task status between active and completed.
    """

    def post(self, request, pk):
        """Handle POST request to toggle task status."""
        # Get task and verify ownership
        task = get_object_or_404(
            Task.objects.select_related('task_list__workspace', 'created_by'),
            pk=pk,
            task_list__workspace__owner=request.user
        )

        # Toggle status
        if task.status == 'active':
            task.mark_complete()
        else:
            task.mark_active()

        # Return updated task card partial
        return render(request, 'tasks/_task_card.html', {'task': task})


class TaskQuickDateView(LoginRequiredMixin, View):
    """
    View for handling quick date actions via HTMX.
    Sets task due_date to today, tomorrow, next week, or clears it.
    """

    def post(self, request, pk):
        """Handle POST request to update task due_date."""
        # Get task and verify ownership
        task = get_object_or_404(
            Task.objects.select_related('task_list__workspace', 'created_by'),
            pk=pk,
            task_list__workspace__owner=request.user
        )

        # Get action from POST data
        action = request.POST.get('action')

        # Calculate new due_date based on action
        if action == 'today':
            task.due_date = date.today()
        elif action == 'tomorrow':
            task.due_date = date.today() + timedelta(days=1)
        elif action == 'next_week':
            # Calculate next Monday
            today = date.today()
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7  # If today is Monday, set to next Monday
            task.due_date = today + timedelta(days=days_until_monday)
        elif action == 'clear':
            task.due_date = None
        else:
            return HttpResponse('Invalid action', status=400)

        # Save task
        task.save(update_fields=['due_date', 'updated_at'])

        # Return updated task card partial
        response = render(request, 'tasks/_task_card.html', {'task': task})
        response['HX-Trigger'] = 'taskUpdated'
        return response


class TaskListView(LoginRequiredMixin, ListView):
    """
    View for displaying all tasks across all workspaces for a user.
    Can be filtered by workspace, tag, status, and due date view via query parameters.
    """
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 50

    def get_queryset(self):
        """Get tasks for the user, filtered by workspace, tag, status, and due date view."""
        # Get or create user preferences
        user_prefs, created = UserPreference.objects.get_or_create(user=self.request.user)

        # Get status filter from query parameter or user preference
        status_filter = self.request.GET.get('status', user_prefs.default_task_status_filter)

        # Update user preference if status filter changed
        if status_filter != user_prefs.default_task_status_filter:
            user_prefs.default_task_status_filter = status_filter
            user_prefs.save(update_fields=['default_task_status_filter'])

        # Base queryset with optimizations
        queryset = Task.objects.filter(
            task_list__workspace__owner=self.request.user,
            is_archived=False
        ).select_related(
            'task_list__workspace',
            'created_by',
            'task_list'
        ).prefetch_related('tags')

        # Apply status filter
        if status_filter == 'active':
            queryset = queryset.filter(status='active')
        elif status_filter == 'completed':
            queryset = queryset.filter(status='completed')
        # 'all' filter shows both active and completed tasks

        # Filter by workspace if specified
        workspace_id = self.request.GET.get('workspace')
        if workspace_id:
            queryset = queryset.filter(task_list__workspace_id=workspace_id)

        # Filter by tag if specified
        tag_name = self.request.GET.get('tag')
        if tag_name:
            queryset = queryset.filter(tags__name=tag_name.strip().lower())

        # Filter by due date view if specified
        view = self.request.GET.get('view')
        if view == 'today':
            today = date.today()
            queryset = queryset.filter(
                status='active',
                due_date=today
            )
        elif view == 'upcoming':
            days = int(self.request.GET.get('days', 7))
            today = date.today()
            end_date = today + timedelta(days=days)
            queryset = queryset.filter(
                status='active',
                due_date__gt=today,
                due_date__lte=end_date
            )
        elif view == 'overdue':
            today = date.today()
            queryset = queryset.filter(
                status='active',
                due_date__lt=today
            )
        elif view == 'no_due_date':
            queryset = queryset.filter(
                status='active',
                due_date__isnull=True
            )

        # Add sort_order annotation for completed task positioning
        queryset = queryset.annotate(
            sort_order=Case(
                When(status='completed', then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('sort_order', '-created_at')

        return queryset

    def get_due_date_counts(self):
        """
        Get task counts for due date views.

        Returns:
            Dictionary with today_count, overdue_count, and upcoming_count
        """
        base_queryset = Task.objects.filter(
            task_list__workspace__owner=self.request.user,
            status='active',
            is_archived=False
        )

        # Apply workspace filter if specified
        workspace_id = self.request.GET.get('workspace')
        if workspace_id:
            base_queryset = base_queryset.filter(task_list__workspace_id=workspace_id)

        # Apply tag filter if specified
        tag_name = self.request.GET.get('tag')
        if tag_name:
            base_queryset = base_queryset.filter(tags__name=tag_name.strip().lower())

        today = date.today()

        return {
            'today_count': base_queryset.filter(due_date=today).count(),
            'overdue_count': base_queryset.filter(due_date__lt=today).count(),
            'upcoming_count': base_queryset.filter(due_date__gt=today).count(),
        }

    def get_status_counts(self):
        """
        Get task counts for status filters.

        Returns:
            Dictionary with active_count, completed_count, and all_count
        """
        base_queryset = Task.objects.filter(
            task_list__workspace__owner=self.request.user,
            is_archived=False
        )

        # Apply workspace filter if specified
        workspace_id = self.request.GET.get('workspace')
        if workspace_id:
            base_queryset = base_queryset.filter(task_list__workspace_id=workspace_id)

        # Apply tag filter if specified
        tag_name = self.request.GET.get('tag')
        if tag_name:
            base_queryset = base_queryset.filter(tags__name=tag_name.strip().lower())

        # Use aggregate with Q filters for single-query counts
        from django.db.models import Count
        counts = base_queryset.aggregate(
            active_count=Count('id', filter=Q(status='active')),
            completed_count=Count('id', filter=Q(status='completed'))
        )

        counts['all_count'] = counts['active_count'] + counts['completed_count']
        counts['total_count'] = counts['all_count']  # Alias for template compatibility

        return counts

    def get_context_data(self, **kwargs):
        """Add filters, counts, and active view to context."""
        context = super().get_context_data(**kwargs)

        # Get or create user preferences
        user_prefs, created = UserPreference.objects.get_or_create(user=self.request.user)

        # Get current status filter
        status_filter = self.request.GET.get('status', user_prefs.default_task_status_filter)
        context['current_status_filter'] = status_filter

        # Get status counts
        context.update(self.get_status_counts())

        # Get current workspace filter
        workspace_id = self.request.GET.get('workspace')
        if workspace_id:
            context['current_workspace'] = get_object_or_404(Workspace, id=workspace_id, owner=self.request.user)

        # Get current tag filter
        tag_name = self.request.GET.get('tag')
        if tag_name:
            context['current_tag'] = tag_name.strip().lower()

        # Get current due date view
        view = self.request.GET.get('view')
        context['active_view'] = view
        context['upcoming_days'] = int(self.request.GET.get('days', 7))

        # Get due date counts for badges
        context.update(self.get_due_date_counts())

        # Build active filters list
        active_filters = []
        if view:
            if view == 'today':
                active_filters.append({'type': 'view', 'label': 'Due Today', 'value': 'today'})
            elif view == 'upcoming':
                days = context['upcoming_days']
                active_filters.append({'type': 'view', 'label': f'Upcoming ({days} days)', 'value': 'upcoming'})
            elif view == 'overdue':
                active_filters.append({'type': 'view', 'label': 'Overdue', 'value': 'overdue'})
            elif view == 'no_due_date':
                active_filters.append({'type': 'view', 'label': 'No Due Date', 'value': 'no_due_date'})

        context['active_filters'] = active_filters

        # Add archived task count
        archived_count = Task.objects.filter(
            task_list__workspace__owner=self.request.user,
            is_archived=True
        ).count()
        context['archived_count'] = archived_count

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
        ).select_related('task_list__workspace', 'created_by', 'task_list').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        """Add workspace and task_list to context."""
        context = super().get_context_data(**kwargs)
        context['workspace'] = self.object.workspace
        context['task_list'] = self.object.task_list

        # Add sidebar counts (required by task_sidebar.html)
        from django.db.models import Q, Count
        from django.utils import timezone

        workspace = self.object.task_list.workspace
        today = timezone.now().date()

        # Get task counts for sidebar
        tasks = Task.objects.filter(
            task_list__workspace=workspace,
            is_archived=False
        )

        context['total_count'] = tasks.count()
        context['active_count'] = tasks.filter(status='active').count()
        context['completed_count'] = tasks.filter(status='completed').count()

        # Due date counts
        context['today_count'] = tasks.filter(due_date=today).count()
        context['today_completed_count'] = tasks.filter(due_date=today, status='completed').count()

        context['upcoming_count'] = tasks.filter(due_date__gt=today).count()
        context['upcoming_completed_count'] = tasks.filter(due_date__gt=today, status='completed').count()

        context['overdue_count'] = tasks.filter(due_date__lt=today, status='active').count()
        context['overdue_completed_count'] = 0

        context['archived_count'] = Task.objects.filter(
            task_list__workspace=workspace,
            is_archived=True
        ).count()

        return context


# ============================================================================
# Bulk Actions & Archive Views
# ============================================================================

class TaskListMarkAllCompleteView(LoginRequiredMixin, WorkspaceAccessMixin, View):
    """
    View for marking all active tasks in a task list as complete.
    Uses atomic transaction to ensure data consistency.
    """

    def dispatch(self, request, *args, **kwargs):
        """Override to get task list and verify workspace access."""
        task_list_id = kwargs.get('pk')
        self.task_list = get_object_or_404(TaskList, id=task_list_id)

        # Verify user owns workspace
        if self.task_list.workspace.owner != request.user:
            raise PermissionDenied("You do not have access to this task list.")

        self.workspace = self.task_list.workspace
        return super(WorkspaceAccessMixin, self).dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        """Handle POST request to mark all active tasks complete."""
        # Use transaction for atomicity
        with transaction.atomic():
            # Get all active, non-archived tasks in this task list
            tasks = Task.objects.filter(
                task_list=self.task_list,
                status='active',
                is_archived=False
            )

            # Count for message
            task_count = tasks.count()

            # Mark all tasks complete using mark_complete() for each task
            for task in tasks:
                task.mark_complete()

        # Return success message
        messages.success(request, f'{task_count} tasks marked complete')

        # Return empty response with HX-Trigger to refresh list
        response = HttpResponse('')
        response['HX-Trigger'] = 'taskListRefresh'
        return response


class TaskArchiveView(LoginRequiredMixin, View):
    """
    View for archiving a single task.
    Sets is_archived=True (soft delete).
    """

    def post(self, request, pk):
        """Handle POST request to archive task."""
        # Get task and verify ownership
        task = get_object_or_404(
            Task.objects.select_related('task_list__workspace'),
            pk=pk,
            task_list__workspace__owner=request.user
        )

        # Archive the task
        task.archive()

        # Return success message
        messages.success(request, 'Task archived')

        # Return empty response with HX-Trigger to remove task from list
        response = HttpResponse('')
        response['HX-Trigger'] = 'taskArchived'
        return response


class TaskUnarchiveView(LoginRequiredMixin, View):
    """
    View for unarchiving a single task.
    Sets is_archived=False to restore task to normal view.
    """

    def post(self, request, pk):
        """Handle POST request to unarchive task."""
        # Get task and verify ownership
        task = get_object_or_404(
            Task.objects.select_related('task_list__workspace'),
            pk=pk,
            task_list__workspace__owner=request.user
        )

        # Unarchive the task
        task.unarchive()

        # Return success message
        messages.success(request, 'Task restored from archive')

        # Return empty response with HX-Trigger to remove task from archive list
        response = HttpResponse('')
        response['HX-Trigger'] = 'taskUnarchived'
        return response


class TaskListArchiveAllCompletedView(LoginRequiredMixin, WorkspaceAccessMixin, View):
    """
    View for archiving all completed tasks in a task list.
    Uses atomic transaction to ensure data consistency.
    """

    def dispatch(self, request, *args, **kwargs):
        """Override to get task list and verify workspace access."""
        task_list_id = kwargs.get('pk')
        self.task_list = get_object_or_404(TaskList, id=task_list_id)

        # Verify user owns workspace
        if self.task_list.workspace.owner != request.user:
            raise PermissionDenied("You do not have access to this task list.")

        self.workspace = self.task_list.workspace
        return super(WorkspaceAccessMixin, self).dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        """Handle POST request to archive all completed tasks."""
        # Use transaction for atomicity
        with transaction.atomic():
            # Get all completed, non-archived tasks in this task list
            tasks = Task.objects.filter(
                task_list=self.task_list,
                status='completed',
                is_archived=False
            )

            # Count for message
            task_count = tasks.count()

            # Archive all tasks using update for efficiency
            tasks.update(is_archived=True)

        # Return success message
        messages.success(request, f'{task_count} tasks archived')

        # Return empty response with HX-Trigger to refresh list
        response = HttpResponse('')
        response['HX-Trigger'] = 'taskListRefresh'
        return response


class ArchivedTaskListView(LoginRequiredMixin, ListView):
    """
    View for displaying archived tasks.
    Shows only tasks where is_archived=True, scoped to user's workspaces.
    """
    model = Task
    template_name = 'tasks/archived_task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        """Get archived tasks for the user."""
        return Task.objects.filter(
            task_list__workspace__owner=self.request.user,
            is_archived=True
        ).select_related(
            'task_list__workspace',
            'created_by',
            'task_list'
        ).prefetch_related('tags').order_by('-completed_at')

    def get_context_data(self, **kwargs):
        """Add archived count and workspace to context."""
        context = super().get_context_data(**kwargs)
        context['archived_count'] = self.get_queryset().count()
        return context
