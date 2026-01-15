"""
Task models for task management.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
import re


class TagManager(models.Manager):
    """Custom manager for common Tag queries."""

    def for_workspace(self, workspace):
        """Return tags for a specific workspace."""
        return self.filter(workspace=workspace)

    def for_user(self, user):
        """Return tags user has access to (via their workspaces)."""
        return self.filter(workspace__owner=user)

    def get_or_create_tag(self, name, workspace, user, color=None):
        """
        Get existing tag or create new one.

        Args:
            name: Tag name (will be cleaned and normalized)
            workspace: Workspace the tag belongs to
            user: User creating the tag
            color: Optional hex color (default: #3B82F6 - blue)

        Returns:
            Tag instance
        """
        # Clean and normalize tag name
        clean_name = name.strip().lower()
        if not clean_name:
            return None

        # Get or create tag
        tag, created = self.get_or_create(
            name=clean_name,
            workspace=workspace,
            defaults={
                'created_by': user,
                'color': color or '#3B82F6'  # Default blue
            }
        )
        return tag

    def popular_for_workspace(self, workspace, limit=10):
        """
        Return most used tags for a workspace.

        Args:
            workspace: Workspace to query
            limit: Maximum number of tags to return

        Returns:
            QuerySet of tags ordered by usage count
        """
        from django.db.models import Count
        return self.filter(workspace=workspace).annotate(
            task_count=Count('tasks')
        ).order_by('-task_count')[:limit]


class Tag(models.Model):
    """
    Tag model for categorizing tasks.

    Tags provide a flexible way to categorize and filter tasks across task lists.
    Each tag belongs to a workspace and can be applied to multiple tasks.
    """

    # Required fields
    name = models.CharField(
        max_length=50,
        help_text="Tag name (max 50 characters)"
    )

    workspace = models.ForeignKey(
        'accounts.Workspace',
        on_delete=models.CASCADE,
        related_name='tags',
        help_text="Workspace this tag belongs to"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tags_created',
        help_text="User who created this tag"
    )

    # Optional fields
    color = models.CharField(
        max_length=7,
        default='#3B82F6',  # Blue
        help_text="Hex color code for tag (e.g., #3B82F6)"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When tag was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When tag was last updated"
    )

    # Custom manager
    objects = TagManager()

    class Meta:
        db_table = 'tags'
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']

        indexes = [
            models.Index(fields=['workspace'], name='tag_workspace_idx'),
            models.Index(fields=['created_by'], name='tag_created_by_idx'),
            models.Index(fields=['name'], name='tag_name_idx'),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'name'],
                name='unique_tag_name_per_workspace'
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

        # Normalize name to lowercase
        if self.name:
            self.name = self.name.strip().lower()

        # Validate color format (hex color)
        if self.color:
            if not re.match(r'^#[0-9A-Fa-f]{6}$', self.color):
                raise ValidationError({
                    'color': 'Color must be a valid hex code (e.g., #3B82F6).'
                })

    def save(self, *args, **kwargs):
        """Override save to ensure clean() is called."""
        self.full_clean()
        super().save(*args, **kwargs)


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

    def upcoming(self, days=7):
        """
        Return tasks due in the next specified number of days (excluding today).

        Args:
            days: Number of days to look ahead (default: 7)

        Returns:
            QuerySet of active tasks due between tomorrow and days from now
        """
        today = date.today()
        tomorrow = today + timedelta(days=1)
        end_date = today + timedelta(days=days)
        return self.filter(
            status='active',
            due_date__gte=tomorrow,
            due_date__lte=end_date
        ).order_by('due_date')

    def no_due_date(self):
        """
        Return active tasks without a due date.

        Returns:
            QuerySet of active tasks with no due_date, ordered by created_at descending
        """
        return self.filter(
            status='active',
            due_date__isnull=True
        ).order_by('-created_at')


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

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When task was marked as completed"
    )

    is_archived = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether task is archived (soft delete)"
    )

    # Tags (many-to-many relationship)
    tags = models.ManyToManyField(
        'Tag',
        related_name='tasks',
        blank=True,
        help_text="Tags for categorizing this task"
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
            models.Index(fields=['task_list', 'status', 'is_archived'], name='task_list_status_archived_idx'),
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
            models.CheckConstraint(
                check=(
                    models.Q(completed_at__isnull=True, status='active') |
                    models.Q(completed_at__isnull=False, status='completed') |
                    models.Q(completed_at__isnull=True, status='completed')
                ),
                name='completed_at_requires_completed_status'
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def workspace(self):
        """Convenient property to access workspace through task_list."""
        return self.task_list.workspace if self.task_list else None

    def mark_complete(self):
        """Mark task as completed and set completion timestamp."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def mark_active(self):
        """Mark task as active (incomplete) and clear completion timestamp."""
        self.status = 'active'
        self.completed_at = None
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def archive(self):
        """Archive task (soft delete)."""
        self.is_archived = True
        self.save(update_fields=['is_archived', 'updated_at'])

    def unarchive(self):
        """Unarchive task (restore from soft delete)."""
        self.is_archived = False
        self.save(update_fields=['is_archived', 'updated_at'])

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

    def get_due_status(self):
        """
        Get the due date status of the task.

        Returns:
            String: 'overdue', 'due_today', 'upcoming', or 'no_due_date'
        """
        if not self.due_date:
            return 'no_due_date'

        if self.status == 'completed':
            return 'no_due_date'

        if self.is_overdue():
            return 'overdue'

        if self.is_due_today():
            return 'due_today'

        return 'upcoming'

    def get_due_status_color(self):
        """
        Get Tailwind CSS color class for due date status.

        Returns:
            String: 'red', 'yellow', 'green', or 'gray'
        """
        status = self.get_due_status()
        colors = {
            'overdue': 'red',
            'due_today': 'yellow',
            'upcoming': 'green',
            'no_due_date': 'gray',
        }
        return colors.get(status, 'gray')

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
