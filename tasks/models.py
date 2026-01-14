"""
Task models for task management.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date


class TaskListManager(models.Manager):
    """Custom manager for common TaskList queries."""

    def for_workspace(self, workspace):
        """Return task lists for a specific workspace."""
        return self.filter(workspace=workspace)

    def for_user(self, user):
        """Return task lists created by a specific user."""
        return self.filter(created_by=user)


class TaskList(models.Model):
    """
    TaskList model for organizing tasks within a workspace.

    TaskLists provide a way to group related tasks together within a workspace,
    allowing users to organize tasks by project, category, or any other criteria.
    """

    # Required fields
    name = models.CharField(
        max_length=255,
        help_text="TaskList name (required)"
    )

    workspace = models.ForeignKey(
        'accounts.Workspace',
        on_delete=models.CASCADE,
        related_name='task_lists',
        help_text="Workspace this task list belongs to"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='task_lists_created',
        help_text="User who created this task list"
    )

    # Optional fields
    description = models.TextField(
        blank=True,
        help_text="TaskList description"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When task list was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When task list was last updated"
    )

    # Custom manager
    objects = TaskListManager()

    class Meta:
        db_table = 'task_lists'
        verbose_name = 'Task List'
        verbose_name_plural = 'Task Lists'
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['workspace'], name='tasklist_workspace_idx'),
            models.Index(fields=['created_by'], name='tasklist_created_by_idx'),
            models.Index(fields=['-created_at'], name='tasklist_created_at_idx'),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'name'],
                name='unique_tasklist_name_per_workspace'
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Model validation."""
        # Name must not be empty or only whitespace
        if self.name and not self.name.strip():
            raise ValidationError({
                'name': 'Name cannot be empty or only whitespace.'
            })


class TaskManager(models.Manager):
    """Custom manager for common Task queries."""

    def active(self):
        """Return only active (non-completed) tasks."""
        return self.filter(status='active')

    def completed(self):
        """Return only completed tasks."""
        return self.filter(status='completed')

    def for_task_list(self, task_list):
        """Return tasks for a specific task list."""
        return self.filter(task_list=task_list)

    def for_workspace(self, workspace):
        """Return tasks for a specific workspace."""
        return self.filter(task_list__workspace=workspace)

    def for_user(self, user):
        """Return tasks created by a specific user."""
        return self.filter(created_by=user)

    def overdue(self):
        """Return tasks that are past their due date."""
        today = date.today()
        return self.filter(
            status='active',
            due_date__lt=today
        )

    def due_today(self):
        """Return tasks due today."""
        today = date.today()
        return self.filter(
            status='active',
            due_date=today
        )


class Task(models.Model):
    """
    Task model for individual to-do items within a task list.

    Tasks are the core entity for task management, containing all information
    needed to track a single piece of work including title, description,
    due dates, priority level, and completion status. Tasks belong to a TaskList,
    which in turn belongs to a Workspace.
    """

    PRIORITY_CHOICES = [
        ('P1', 'Urgent'),
        ('P2', 'High'),
        ('P3', 'Medium'),
        ('P4', 'Low'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    # Required fields
    title = models.CharField(
        max_length=255,
        help_text="Task title (required)"
    )

    priority = models.CharField(
        max_length=2,
        choices=PRIORITY_CHOICES,
        help_text="Task priority level (P1=Urgent, P2=High, P3=Medium, P4=Low)"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Current task status"
    )

    task_list = models.ForeignKey(
        'TaskList',
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text="Task list this task belongs to"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks_created',
        help_text="User who created this task"
    )

    # Optional fields
    description = models.TextField(
        blank=True,
        help_text="Task description with markdown support"
    )

    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when task is due"
    )

    due_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Specific time for deadline (requires due_date)"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When task was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When task was last updated"
    )

    # Custom manager
    objects = TaskManager()

    class Meta:
        db_table = 'tasks'
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['task_list', 'status'], name='task_tasklist_status_idx'),
            models.Index(fields=['due_date'], name='task_due_date_idx'),
            models.Index(fields=['priority'], name='task_priority_idx'),
            models.Index(fields=['created_by'], name='task_created_by_idx'),
            models.Index(fields=['-created_at'], name='task_created_at_idx'),
            models.Index(fields=['task_list', 'created_by'], name='task_tasklist_user_idx'),
        ]

        constraints = [
            models.CheckConstraint(
                check=models.Q(priority__in=['P1', 'P2', 'P3', 'P4']),
                name='valid_priority'
            ),
            models.CheckConstraint(
                check=models.Q(status__in=['active', 'completed']),
                name='valid_status'
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def workspace(self):
        """Convenient property to access workspace through task_list."""
        return self.task_list.workspace if self.task_list else None

    def mark_complete(self):
        """Mark task as completed."""
        self.status = 'completed'
        self.save(update_fields=['status', 'updated_at'])

    def mark_active(self):
        """Mark task as active (incomplete)."""
        self.status = 'active'
        self.save(update_fields=['status', 'updated_at'])

    def is_overdue(self):
        """Check if task is overdue."""
        if not self.due_date or self.status == 'completed':
            return False
        return self.due_date < date.today()

    def is_due_today(self):
        """Check if task is due today."""
        if not self.due_date or self.status == 'completed':
            return False
        return self.due_date == date.today()

    def get_priority_display_color(self):
        """Get Tailwind CSS color class for priority."""
        colors = {
            'P1': 'red',    # Urgent - Red
            'P2': 'orange', # High - Orange
            'P3': 'yellow', # Medium - Yellow
            'P4': 'blue',   # Low - Blue
        }
        return colors.get(self.priority, 'gray')

    def clean(self):
        """Model validation."""
        # If due_time is set, due_date must also be set
        if self.due_time and not self.due_date:
            raise ValidationError({
                'due_time': 'Cannot set due time without a due date.'
            })

        # Title must not be empty or only whitespace
        if self.title and not self.title.strip():
            raise ValidationError({
                'title': 'Title cannot be empty or only whitespace.'
            })
