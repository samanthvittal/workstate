"""
Task models for task management.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.postgres.search import SearchVectorField, SearchQuery, SearchRank
from django.contrib.postgres.indexes import GinIndex
from django.db.models import F, Q
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

    def search_tasks(self, user, query, filters=None):
        """
        Search tasks using full-text search with permission filtering.

        Args:
            user: User performing the search
            query: Sanitized search query string (tsquery format)
            filters: Optional dict with keys: workspace_id, tag_names, status, priority

        Returns:
            QuerySet of tasks annotated with relevance score, ordered by relevance
        """
        from tasks.services import SearchQueryService

        if not query or not query.strip():
            # Return empty queryset for empty queries
            return self.none()

        # Sanitize and parse the query
        tsquery_string = SearchQueryService.parse_search_query(query)
        if not tsquery_string:
            return self.none()

        # Create the search query using PostgreSQL to_tsquery
        search_query = SearchQuery(tsquery_string, search_type='raw', config='english')

        # Base queryset filtered by user's accessible workspaces
        queryset = self.filter(
            task_list__workspace__owner=user,
            is_archived=False
        ).filter(
            search_vector=search_query
        ).select_related(
            'task_list__workspace',
            'created_by'
        ).prefetch_related(
            'tags'
        )

        # Annotate with relevance score using ts_rank_cd
        queryset = queryset.annotate(
            relevance=SearchRank(F('search_vector'), search_query)
        )

        # Apply filters if provided
        if filters:
            queryset = self._apply_search_filters(queryset, filters, user)

        # Default sort by relevance
        queryset = queryset.order_by('-relevance', '-created_at')

        return queryset

    def _apply_search_filters(self, queryset, filters, user):
        """
        Apply additional filters to search results.

        Args:
            queryset: QuerySet to filter
            filters: Dict with filter options
            user: User performing search (for permission validation)

        Returns:
            Filtered QuerySet
        """
        # Filter by workspace
        if 'workspace_id' in filters and filters['workspace_id']:
            # Validate user has access to this workspace
            queryset = queryset.filter(
                task_list__workspace_id=filters['workspace_id'],
                task_list__workspace__owner=user
            )

        # Filter by tags
        if 'tag_names' in filters and filters['tag_names']:
            tag_names = filters['tag_names']
            if isinstance(tag_names, str):
                tag_names = [tag_names]
            queryset = queryset.filter(tags__name__in=tag_names).distinct()

        # Filter by status
        if 'status' in filters and filters['status']:
            status = filters['status']
            if status in ('active', 'completed'):
                queryset = queryset.filter(status=status)
            # 'all' or any other value means no status filter

        # Filter by priority
        if 'priority' in filters and filters['priority']:
            priorities = filters['priority']
            if isinstance(priorities, str):
                priorities = [priorities]
            # Validate priorities are in valid choices
            valid_priorities = [p for p in priorities if p in ('P1', 'P2', 'P3', 'P4')]
            if valid_priorities:
                queryset = queryset.filter(priority__in=valid_priorities)

        return queryset

    def apply_search_sort(self, queryset, sort_option='relevance'):
        """
        Apply sorting to search results queryset.

        Args:
            queryset: QuerySet to sort (must have 'relevance' annotation)
            sort_option: Sort option ('relevance', 'due_date', 'priority', 'created_at')

        Returns:
            Sorted QuerySet
        """
        sort_mapping = {
            'relevance': ['-relevance', '-created_at'],
            'due_date': ['due_date', '-created_at'],
            'priority': ['priority', '-created_at'],
            'created_at': ['-created_at', '-relevance'],
        }

        sort_fields = sort_mapping.get(sort_option, sort_mapping['relevance'])
        return queryset.order_by(*sort_fields)


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

    # Full-text search vector field
    search_vector = SearchVectorField(
        null=True,
        blank=True,
        help_text="Full-text search vector for title and description"
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
            GinIndex(fields=['search_vector'], name='task_search_vector_idx'),
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

    def has_active_timer(self, user):
        """
        Check if this task has an active timer for the given user.

        Args:
            user: User to check timer for

        Returns:
            bool: True if task has an active timer for this user
        """
        from time_tracking.models import TimeEntry
        return TimeEntry.objects.filter(
            task=self,
            user=user,
            is_running=True
        ).exists()

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

    def get_search_snippet(self, query, max_length=150):
        """
        Generate a search snippet with highlighted terms using PostgreSQL ts_headline.

        Args:
            query: Search query string
            max_length: Maximum length of snippet in characters

        Returns:
            String with highlighted search terms wrapped in <mark> tags
        """
        from django.db import connection
        from tasks.services import SearchQueryService

        # Sanitize query
        tsquery_string = SearchQueryService.parse_search_query(query)
        if not tsquery_string:
            # Fallback to truncated description
            if self.description:
                return self.description[:max_length] + ('...' if len(self.description) > max_length else '')
            return self.title

        # Use ts_headline to generate snippet
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ts_headline('english', %s, to_tsquery('english', %s),
                    'MaxWords=20, MinWords=10, ShortWord=3, HighlightAll=FALSE,
                     StartSel=<mark>, StopSel=</mark>')
                """,
                [self.description or self.title, tsquery_string]
            )
            result = cursor.fetchone()
            if result and result[0]:
                snippet = result[0]
                # Limit length if necessary
                if len(snippet) > max_length:
                    snippet = snippet[:max_length] + '...'
                return snippet

        # Fallback
        return self.description[:max_length] if self.description else self.title

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


class SearchHistoryManager(models.Manager):
    """Custom manager for SearchHistory queries."""

    def get_recent_for_user(self, user, limit=10):
        """
        Get recent search history for a user.

        Args:
            user: User object
            limit: Maximum number of searches to return

        Returns:
            QuerySet of recent searches ordered by searched_at descending
        """
        return self.filter(user=user).order_by('-searched_at')[:limit]

    def prune_old_searches(self, user, keep_count=50):
        """
        Prune old search history for a user, keeping only the most recent entries.

        Args:
            user: User object
            keep_count: Number of most recent searches to keep (default: 50)
        """
        searches = self.filter(user=user).order_by('-searched_at')
        total_count = searches.count()

        if total_count > keep_count:
            # Get the IDs of searches to delete
            searches_to_delete = searches[keep_count:]
            delete_ids = list(searches_to_delete.values_list('id', flat=True))

            # Delete old searches
            self.filter(id__in=delete_ids).delete()


class SearchHistory(models.Model):
    """
    Search history model for tracking user search queries.

    Stores user search queries with result counts and timestamps
    for displaying recent searches and analytics.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='search_history',
        help_text="User who performed the search"
    )

    query = models.CharField(
        max_length=255,
        help_text="Search query string"
    )

    result_count = models.IntegerField(
        default=0,
        help_text="Number of results returned for this search"
    )

    searched_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the search was performed"
    )

    # Custom manager
    objects = SearchHistoryManager()

    class Meta:
        db_table = 'search_history'
        verbose_name = 'Search History'
        verbose_name_plural = 'Search Histories'
        ordering = ['-searched_at']

        indexes = [
            models.Index(fields=['user'], name='search_history_user_idx'),
            models.Index(fields=['user', '-searched_at'], name='search_history_user_date_idx'),
        ]

    def __str__(self):
        return f"{self.user.email}: {self.query} ({self.result_count} results)"


class SavedSearchManager(models.Manager):
    """Custom manager for SavedSearch queries."""

    def for_user(self, user):
        """Return saved searches for a specific user."""
        return self.filter(user=user).order_by('-created_at')


class SavedSearch(models.Model):
    """
    Saved search model for storing user's frequently used searches.

    Stores search queries with filter configurations to allow users
    to quickly re-execute complex searches.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_searches',
        help_text="User who saved this search"
    )

    name = models.CharField(
        max_length=100,
        help_text="Name for this saved search"
    )

    query = models.TextField(
        help_text="Search query string"
    )

    filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Filter configuration (workspace_id, tag_names, status, priority, date_range)"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the search was saved"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the search was last updated"
    )

    # Custom manager
    objects = SavedSearchManager()

    class Meta:
        db_table = 'saved_searches'
        verbose_name = 'Saved Search'
        verbose_name_plural = 'Saved Searches'
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['user'], name='saved_search_user_idx'),
            models.Index(fields=['user', 'name'], name='saved_search_user_name_idx'),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name='unique_saved_search_name_per_user'
            ),
        ]

    def __str__(self):
        return f"{self.user.email}: {self.name}"

    def clean(self):
        """Model validation."""
        # Name must not be empty or only whitespace
        if self.name and not self.name.strip():
            raise ValidationError({
                'name': 'Name cannot be empty or only whitespace.'
            })

        # Validate user has not exceeded 20 saved searches
        if not self.pk:  # Only check on creation
            existing_count = SavedSearch.objects.filter(user=self.user).count()
            if existing_count >= 20:
                raise ValidationError({
                    'user': 'Cannot save more than 20 searches. Please delete an existing search first.'
                })

    def save(self, *args, **kwargs):
        """Override save to ensure clean() is called."""
        self.full_clean()
        super().save(*args, **kwargs)
