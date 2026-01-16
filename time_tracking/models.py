"""
Time tracking models for managing timers, time entries, and time goals.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class TimeEntryManager(models.Manager):
    """Custom manager for TimeEntry queries."""

    def running(self):
        """Return only active timers."""
        return self.filter(is_running=True)

    def for_user(self, user):
        """Return time entries for a specific user with permission checks."""
        return self.filter(user=user)


class TimeEntry(models.Model):
    """
    TimeEntry model for tracking time spent on tasks.

    Supports both timer-based tracking (start_time/end_time) and manual duration entry.
    Enforces single active timer per user at database and application level.
    """

    # Required fields
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='time_entries',
        help_text="User who owns this time entry"
    )

    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        related_name='time_entries',
        help_text="Task this time entry is linked to (required)"
    )

    project = models.ForeignKey(
        'tasks.TaskList',
        on_delete=models.CASCADE,
        related_name='time_entries',
        null=True,
        blank=True,
        help_text="Project (TaskList) inherited from task"
    )

    duration = models.DurationField(
        help_text="Total duration of time entry (required)"
    )

    # Timer fields (nullable for manual entries)
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When timer was started (nullable for duration-only entries)"
    )

    end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When timer was stopped (nullable for running or duration-only entries)"
    )

    # Timer state
    is_running = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether timer is currently running"
    )

    # Optional fields
    description = models.TextField(
        blank=True,
        help_text="Additional notes or description for this time entry"
    )

    # Billable tracking
    is_billable = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this time entry is billable"
    )

    billable_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Hourly rate for billing (nullable)"
    )

    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency code for billing (ISO 4217)"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When time entry was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When time entry was last updated"
    )

    # Custom manager
    objects = TimeEntryManager()

    class Meta:
        db_table = 'time_entries'
        verbose_name = 'Time Entry'
        verbose_name_plural = 'Time Entries'
        ordering = ['-start_time', '-created_at']

        indexes = [
            models.Index(fields=['user'], name='time_entry_user_idx'),
            models.Index(fields=['task'], name='time_entry_task_idx'),
            models.Index(fields=['project'], name='time_entry_project_idx'),
            models.Index(fields=['start_time'], name='time_entry_start_time_idx'),
            models.Index(fields=['is_running'], name='time_entry_is_running_idx'),
            models.Index(fields=['is_billable'], name='time_entry_is_billable_idx'),
            models.Index(fields=['user', 'start_time'], name='time_entry_user_start_idx'),
        ]

        constraints = [
            models.CheckConstraint(
                check=models.Q(end_time__isnull=True) | models.Q(start_time__isnull=True) | models.Q(end_time__gt=models.F('start_time')),
                name='end_time_after_start_time'
            ),
            models.CheckConstraint(
                check=models.Q(duration__gte=timedelta(0)),
                name='non_negative_duration'
            ),
        ]

    def __str__(self):
        task_title = self.task.title if self.task_id else 'No Task'
        return f"{self.user.email} - {task_title} - {self.duration}"

    def clean(self):
        """Model validation."""
        # Task is required - only check if task_id is not set
        if not self.task_id:
            raise ValidationError({
                'task': 'Task is required for all time entries.'
            })

        # Validate end_time > start_time if both present
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError({
                    'end_time': 'End time must be after start time.'
                })

        # Validate duration is non-negative (allow 0 for running timers)
        if self.duration is not None and self.duration < timedelta(0):
            raise ValidationError({
                'duration': 'Duration cannot be negative.'
            })

        # Validate positive duration for stopped timers
        if not self.is_running and self.duration is not None and self.duration <= timedelta(0):
            raise ValidationError({
                'duration': 'Duration must be positive for stopped timers.'
            })

        # Validate single active timer per user (application-level check)
        if self.is_running:
            existing_running = TimeEntry.objects.filter(
                user=self.user,
                is_running=True
            ).exclude(pk=self.pk)

            if existing_running.exists():
                raise ValidationError({
                    'is_running': 'Only one timer can be running at a time. Stop the current timer first.'
                })

    def save(self, *args, **kwargs):
        """Override save to ensure clean() is called and project is inherited."""
        # Inherit project from task before validation (only if task is already set)
        if self.task_id and not self.project_id:
            # Need to fetch the task to get the task_list
            if not hasattr(self, '_task_obj'):
                from tasks.models import Task
                try:
                    task_obj = Task.objects.select_related('task_list').get(pk=self.task_id)
                    self.project = task_obj.task_list
                except Task.DoesNotExist:
                    pass

        self.full_clean()
        super().save(*args, **kwargs)

    def calculate_duration(self):
        """
        Calculate duration based on start_time and end_time.

        Returns:
            timedelta: Calculated duration, or None if times not set
        """
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    def stop(self, end_time=None):
        """
        Stop the running timer and calculate final duration.

        Args:
            end_time: Optional end time (defaults to now)
        """
        if not self.is_running:
            raise ValidationError('Timer is not running.')

        if not end_time:
            end_time = timezone.now()

        self.end_time = end_time
        self.is_running = False

        # Calculate and set duration
        if self.start_time:
            self.duration = end_time - self.start_time

        self.save(update_fields=['end_time', 'is_running', 'duration', 'updated_at'])

    def get_elapsed_time(self):
        """
        Get elapsed time for running timer.

        Returns:
            timedelta: Elapsed time from start_time to now, or duration if stopped
        """
        if self.is_running and self.start_time:
            return timezone.now() - self.start_time
        return self.duration

    def apply_rounding(self, interval_minutes, method='nearest'):
        """
        Apply time rounding to duration.

        Args:
            interval_minutes: Rounding interval in minutes (5, 10, 15, 30)
            method: Rounding method ('up', 'down', 'nearest')

        Returns:
            timedelta: Rounded duration
        """
        if not self.duration or interval_minutes == 0:
            return self.duration

        total_minutes = self.duration.total_seconds() / 60
        interval = interval_minutes

        if method == 'up':
            rounded_minutes = int(((total_minutes + interval - 1) // interval) * interval)
        elif method == 'down':
            rounded_minutes = int((total_minutes // interval) * interval)
        else:  # nearest
            rounded_minutes = int(round(total_minutes / interval) * interval)

        return timedelta(minutes=rounded_minutes)


class TimeEntryTag(models.Model):
    """
    Many-to-many relationship model between TimeEntry and Tag.

    Allows tagging time entries for categorization and filtering.
    """

    time_entry = models.ForeignKey(
        TimeEntry,
        on_delete=models.CASCADE,
        related_name='time_entry_tags',
        help_text="Time entry being tagged"
    )

    tag = models.ForeignKey(
        'tasks.Tag',
        on_delete=models.CASCADE,
        related_name='time_entry_tags',
        help_text="Tag applied to time entry"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When tag was applied"
    )

    class Meta:
        db_table = 'time_entry_tags'
        verbose_name = 'Time Entry Tag'
        verbose_name_plural = 'Time Entry Tags'
        unique_together = [['time_entry', 'tag']]

        indexes = [
            models.Index(fields=['time_entry'], name='time_entry_tag_entry_idx'),
            models.Index(fields=['tag'], name='time_entry_tag_tag_idx'),
        ]

    def __str__(self):
        return f"{self.time_entry} - {self.tag}"


class TimeGoal(models.Model):
    """
    TimeGoal model for setting time budgets on projects or tasks.

    Supports daily, weekly, monthly, or total time goals to help users
    track progress against budgeted time.
    """

    GOAL_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('total', 'Total'),
    ]

    # Required fields
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='time_goals',
        help_text="User who set this goal"
    )

    goal_type = models.CharField(
        max_length=10,
        choices=GOAL_TYPE_CHOICES,
        help_text="Type of goal (daily/weekly/monthly/total)"
    )

    target_duration = models.DurationField(
        help_text="Target time duration for this goal"
    )

    # Project or task (mutually exclusive)
    project = models.ForeignKey(
        'tasks.TaskList',
        on_delete=models.CASCADE,
        related_name='time_goals',
        null=True,
        blank=True,
        help_text="Project this goal applies to (mutually exclusive with task)"
    )

    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        related_name='time_goals',
        null=True,
        blank=True,
        help_text="Task this goal applies to (mutually exclusive with project)"
    )

    # Optional date range
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Start date for goal (optional)"
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date for goal (optional)"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this goal is currently active"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When goal was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When goal was last updated"
    )

    class Meta:
        db_table = 'time_goals'
        verbose_name = 'Time Goal'
        verbose_name_plural = 'Time Goals'
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['user'], name='time_goal_user_idx'),
            models.Index(fields=['project'], name='time_goal_project_idx'),
            models.Index(fields=['task'], name='time_goal_task_idx'),
            models.Index(fields=['goal_type'], name='time_goal_type_idx'),
            models.Index(fields=['is_active'], name='time_goal_is_active_idx'),
        ]

    def __str__(self):
        target = self.project or self.task
        return f"{self.user.email} - {self.goal_type} goal for {target}"

    def clean(self):
        """Model validation."""
        # Must have either project or task, but not both
        if self.project and self.task:
            raise ValidationError(
                'Time goal must be for either a project or a task, not both.'
            )

        if not self.project and not self.task:
            raise ValidationError(
                'Time goal must be for either a project or a task.'
            )

        # Target duration must be positive
        if self.target_duration and self.target_duration <= timedelta(0):
            raise ValidationError({
                'target_duration': 'Target duration must be positive.'
            })

        # End date must be after start date if both present
        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValidationError({
                    'end_date': 'End date must be after start date.'
                })

    def save(self, *args, **kwargs):
        """Override save to ensure clean() is called."""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_progress(self):
        """
        Calculate actual time spent towards this goal.

        Returns:
            timedelta: Total time spent on project/task in goal period
        """
        from django.db.models import Sum

        # Build base queryset
        if self.project:
            entries = TimeEntry.objects.filter(
                user=self.user,
                project=self.project,
                is_running=False
            )
        else:
            entries = TimeEntry.objects.filter(
                user=self.user,
                task=self.task,
                is_running=False
            )

        # Apply date filters based on goal type
        if self.goal_type == 'daily':
            from datetime import date
            entries = entries.filter(start_time__date=date.today())
        elif self.goal_type == 'weekly':
            from datetime import date, timedelta
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())
            entries = entries.filter(start_time__date__gte=start_of_week)
        elif self.goal_type == 'monthly':
            from datetime import date
            today = date.today()
            entries = entries.filter(
                start_time__year=today.year,
                start_time__month=today.month
            )
        elif self.goal_type == 'total':
            if self.start_date:
                entries = entries.filter(start_time__date__gte=self.start_date)
            if self.end_date:
                entries = entries.filter(start_time__date__lte=self.end_date)

        # Sum durations
        result = entries.aggregate(total=Sum('duration'))
        return result['total'] or timedelta(0)

    def get_percentage_complete(self):
        """
        Calculate percentage of goal completed.

        Returns:
            float: Percentage (0-100+) of target duration achieved
        """
        progress = self.get_progress()
        if not self.target_duration or self.target_duration == timedelta(0):
            return 0.0

        progress_seconds = progress.total_seconds()
        target_seconds = self.target_duration.total_seconds()

        return (progress_seconds / target_seconds) * 100

    def is_overbudget(self):
        """
        Check if time spent exceeds target.

        Returns:
            bool: True if progress > target_duration
        """
        return self.get_progress() > self.target_duration


class UserTimePreferences(models.Model):
    """
    User preferences for time tracking behavior.

    Stores settings for time rounding, idle detection, Pomodoro timers,
    and default billable rates.
    """

    ROUNDING_INTERVAL_CHOICES = [
        (0, 'No rounding'),
        (5, '5 minutes'),
        (10, '10 minutes'),
        (15, '15 minutes'),
        (30, '30 minutes'),
    ]

    ROUNDING_METHOD_CHOICES = [
        ('up', 'Round up'),
        ('down', 'Round down'),
        ('nearest', 'Round to nearest'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='time_preferences',
        primary_key=True,
        help_text="User these preferences belong to"
    )

    # Time rounding settings
    rounding_interval = models.IntegerField(
        choices=ROUNDING_INTERVAL_CHOICES,
        default=0,
        help_text="Time rounding interval in minutes (0 = no rounding)"
    )

    rounding_method = models.CharField(
        max_length=10,
        choices=ROUNDING_METHOD_CHOICES,
        default='nearest',
        help_text="Method for rounding time (up/down/nearest)"
    )

    # Idle detection settings
    idle_threshold_minutes = models.IntegerField(
        default=5,
        help_text="Minutes of inactivity before idle detection triggers"
    )

    # Pomodoro settings
    pomodoro_work_minutes = models.IntegerField(
        default=25,
        help_text="Length of Pomodoro work interval in minutes"
    )

    pomodoro_break_minutes = models.IntegerField(
        default=5,
        help_text="Length of Pomodoro break interval in minutes"
    )

    # Billable rate defaults
    default_billable_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Default hourly billable rate"
    )

    default_currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Default currency for billing (ISO 4217)"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When preferences were created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When preferences were last updated"
    )

    class Meta:
        db_table = 'user_time_preferences'
        verbose_name = 'User Time Preferences'
        verbose_name_plural = 'User Time Preferences'

    def __str__(self):
        return f"{self.user.email}'s time tracking preferences"

    def clean(self):
        """Model validation."""
        # All minute/interval fields must be positive
        if self.idle_threshold_minutes and self.idle_threshold_minutes < 0:
            raise ValidationError({
                'idle_threshold_minutes': 'Idle threshold must be positive.'
            })

        if self.pomodoro_work_minutes and self.pomodoro_work_minutes < 0:
            raise ValidationError({
                'pomodoro_work_minutes': 'Pomodoro work interval must be positive.'
            })

        if self.pomodoro_break_minutes and self.pomodoro_break_minutes < 0:
            raise ValidationError({
                'pomodoro_break_minutes': 'Pomodoro break interval must be positive.'
            })

        if self.default_billable_rate and self.default_billable_rate < 0:
            raise ValidationError({
                'default_billable_rate': 'Default billable rate must be positive.'
            })

    def save(self, *args, **kwargs):
        """Override save to ensure clean() is called."""
        self.full_clean()
        super().save(*args, **kwargs)


class PomodoroSession(models.Model):
    """
    PomodoroSession model for tracking Pomodoro technique intervals.

    Links to TimeEntry to track multiple Pomodoro sessions within a single
    time tracking session.
    """

    time_entry = models.ForeignKey(
        TimeEntry,
        on_delete=models.CASCADE,
        related_name='pomodoro_sessions',
        help_text="Time entry this Pomodoro session belongs to"
    )

    session_number = models.IntegerField(
        help_text="Sequential number of this Pomodoro session (1, 2, 3...)"
    )

    started_at = models.DateTimeField(
        help_text="When this Pomodoro session started"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this Pomodoro session was completed"
    )

    was_completed = models.BooleanField(
        default=False,
        help_text="Whether this session was completed successfully"
    )

    break_taken = models.BooleanField(
        default=False,
        help_text="Whether user took a break after this session"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )

    class Meta:
        db_table = 'pomodoro_sessions'
        verbose_name = 'Pomodoro Session'
        verbose_name_plural = 'Pomodoro Sessions'
        ordering = ['time_entry', 'session_number']

        indexes = [
            models.Index(fields=['time_entry'], name='pomodoro_time_entry_idx'),
            models.Index(fields=['started_at'], name='pomodoro_started_at_idx'),
        ]

        unique_together = [['time_entry', 'session_number']]

    def __str__(self):
        return f"Pomodoro #{self.session_number} for {self.time_entry}"

    def complete_session(self):
        """Mark session as completed."""
        self.was_completed = True
        self.completed_at = timezone.now()
        self.save(update_fields=['was_completed', 'completed_at'])

    def mark_break_taken(self):
        """Mark that user took a break after this session."""
        self.break_taken = True
        self.save(update_fields=['break_taken'])


class IdleTimeNotification(models.Model):
    """
    IdleTimeNotification model for tracking idle time detection events.

    Created when a running timer exceeds the user's idle threshold.
    Stores the user's action (keep/discard/stop) taken on idle time.
    """

    ACTION_CHOICES = [
        ('none', 'No action taken'),
        ('keep', 'Keep time'),
        ('discard', 'Discard idle time'),
        ('stop_at_idle', 'Stop timer at idle start'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='idle_time_notifications',
        help_text="User who received this notification"
    )

    time_entry = models.ForeignKey(
        TimeEntry,
        on_delete=models.CASCADE,
        related_name='idle_notifications',
        help_text="Time entry that was idle"
    )

    idle_start_time = models.DateTimeField(
        help_text="When idle period started (timer_start + idle_threshold)"
    )

    notification_sent_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When notification was created and sent"
    )

    action_taken = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        default='none',
        db_index=True,
        help_text="Action user took on this notification"
    )

    action_taken_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user took action on this notification"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When notification record was created"
    )

    class Meta:
        db_table = 'idle_time_notifications'
        verbose_name = 'Idle Time Notification'
        verbose_name_plural = 'Idle Time Notifications'
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['user'], name='idle_notif_user_idx'),
            models.Index(fields=['time_entry'], name='idle_notif_time_entry_idx'),
            models.Index(fields=['action_taken'], name='idle_notif_action_idx'),
            models.Index(fields=['user', 'action_taken'], name='idle_notif_user_action_idx'),
        ]

    def __str__(self):
        return f"Idle notification for {self.user.email} - {self.time_entry}"

    def mark_action(self, action, action_time=None):
        """
        Mark the action taken on this notification.

        Args:
            action: One of 'keep', 'discard', 'stop_at_idle'
            action_time: When action was taken (defaults to now)
        """
        if action not in ['keep', 'discard', 'stop_at_idle']:
            raise ValidationError(f"Invalid action: {action}")

        self.action_taken = action
        self.action_taken_at = action_time or timezone.now()
        self.save(update_fields=['action_taken', 'action_taken_at'])
