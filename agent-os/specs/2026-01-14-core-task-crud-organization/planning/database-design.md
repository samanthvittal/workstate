# Database Design: Task Model

## Overview

This document defines the database schema for the Task model following Django and PostgreSQL best practices.

## Task Table Schema

### Table Name
`tasks` (lowercase plural, Django convention)

### Fields

| Field Name | Type | Constraints | Index | Description |
|------------|------|-------------|-------|-------------|
| `id` | BigAutoField | PRIMARY KEY | ✓ | Auto-incrementing primary key |
| `title` | CharField(255) | NOT NULL | - | Task title (required) |
| `description` | TextField | NULL | - | Task description with markdown support |
| `due_date` | DateField | NULL | ✓ | When task is due (nullable) |
| `due_time` | TimeField | NULL | - | Specific time for deadline (nullable) |
| `priority` | CharField(2) | NOT NULL, CHECK | ✓ | Priority level: P1, P2, P3, P4 |
| `status` | CharField(20) | NOT NULL, DEFAULT='active' | ✓ | Task status: active, completed |
| `workspace_id` | BigInteger | FOREIGN KEY, NOT NULL, CASCADE | ✓ | Reference to workspaces table |
| `project_id` | BigInteger | FOREIGN KEY, NULL, CASCADE | ✓ | Reference to projects table (future) |
| `created_by_id` | Integer | FOREIGN KEY, NOT NULL, CASCADE | ✓ | Reference to auth_user table |
| `created_at` | DateTimeField | NOT NULL, AUTO | ✓ | When task was created |
| `updated_at` | DateTimeField | NOT NULL, AUTO | - | When task was last updated |

### Constraints

#### Check Constraints
```sql
-- Priority must be one of the valid values
CHECK (priority IN ('P1', 'P2', 'P3', 'P4'))

-- Status must be one of the valid values
CHECK (status IN ('active', 'completed'))

-- If due_time is set, due_date must also be set
CHECK (due_time IS NULL OR due_date IS NOT NULL)
```

#### Foreign Key Constraints
```sql
-- Workspace relationship (CASCADE delete)
FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE

-- User relationship (CASCADE delete)
FOREIGN KEY (created_by_id) REFERENCES auth_user(id) ON DELETE CASCADE

-- Project relationship (SET NULL on delete) - for future use
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
```

### Indexes

```sql
-- Composite index for workspace + status queries
CREATE INDEX idx_tasks_workspace_status ON tasks(workspace_id, status);

-- Index for due date queries (overdue, upcoming)
CREATE INDEX idx_tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL;

-- Index for priority filtering
CREATE INDEX idx_tasks_priority ON tasks(priority);

-- Index for created_by (user's tasks)
CREATE INDEX idx_tasks_created_by ON tasks(created_by_id);

-- Index for created_at (sorting, recent tasks)
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);

-- Composite index for common query: user's tasks in workspace
CREATE INDEX idx_tasks_workspace_user ON tasks(workspace_id, created_by_id);
```

## Django Model Definition

```python
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date


class TaskManager(models.Manager):
    """Custom manager for common Task queries."""

    def active(self):
        """Return only active (non-completed) tasks."""
        return self.filter(status='active')

    def completed(self):
        """Return only completed tasks."""
        return self.filter(status='completed')

    def for_workspace(self, workspace):
        """Return tasks for a specific workspace."""
        return self.filter(workspace=workspace)

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
    Task model for individual to-do items within a workspace.

    Tasks are the core entity for task management, containing all information
    needed to track a single piece of work including title, description,
    due dates, priority level, and completion status.
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

    workspace = models.ForeignKey(
        'accounts.Workspace',
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text="Workspace this task belongs to"
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

    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        help_text="Project this task belongs to (optional, for future use)"
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
            models.Index(fields=['workspace', 'status'], name='task_workspace_status_idx'),
            models.Index(fields=['due_date'], name='task_due_date_idx'),
            models.Index(fields=['priority'], name='task_priority_idx'),
            models.Index(fields=['created_by'], name='task_created_by_idx'),
            models.Index(fields=['-created_at'], name='task_created_at_idx'),
            models.Index(fields=['workspace', 'created_by'], name='task_workspace_user_idx'),
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
        from django.core.exceptions import ValidationError

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
```

## Migration Strategy

### Step 1: Create tasks app
```bash
python manage.py startapp tasks
```

### Step 2: Add to INSTALLED_APPS
```python
INSTALLED_APPS = [
    # ...
    'tasks.apps.TasksConfig',
]
```

### Step 3: Create initial migration
```bash
python manage.py makemigrations tasks
```

### Step 4: Review migration
Check the generated migration file for correctness

### Step 5: Apply migration
```bash
python manage.py migrate tasks
```

## Notes

### Project Reference
- The `project` field references a `projects.Project` model that doesn't exist yet
- This field is nullable and will be used in future iterations
- For now, it will remain NULL for all tasks

### Performance Considerations
- Composite indexes on (workspace_id, status) for efficient filtering
- Partial index on due_date (only non-NULL values)
- Descending index on created_at for recent tasks queries

### Data Integrity
- CASCADE delete: When workspace or user is deleted, tasks are deleted
- SET NULL: When project is deleted (future), task remains but project reference is removed
- Check constraints ensure only valid priority and status values

### Future Enhancements (Not in This Iteration)
- `position` field for manual ordering (deferred)
- `section_id` foreign key (deferred to Project Management)
- `tags` ManyToMany relationship (deferred)
- `assigned_to` foreign key (deferred to collaboration features)
