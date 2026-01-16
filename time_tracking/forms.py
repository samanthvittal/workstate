"""
Forms for time entry creation and editing.
"""
from django import forms
from django.core.exceptions import ValidationError
from datetime import timedelta, datetime
from decimal import Decimal
from time_tracking.models import TimeEntry, TimeEntryTag, UserTimePreferences
from tasks.models import Task, Tag


class TimeEntryForm(forms.ModelForm):
    """
    Form for creating and editing time entries.

    Supports three input modes:
    - Mode A: start_time + end_time (calculate duration)
    - Mode B: start_time + duration (calculate end_time)
    - Mode C: duration only (no timestamps)

    Applies time rounding rules from user preferences.
    """

    # Duration input as text field (HH:MM or decimal hours)
    duration_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., 2:30 or 2.5',
            'x-model': 'durationInput',
            '@input': 'onDurationChange()',
        }),
        label='Duration',
        help_text='Enter duration as HH:MM (e.g., 2:30) or decimal hours (e.g., 2.5)',
    )

    # Custom field for tag input (comma-separated tag names)
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., work, urgent, client-a',
            'maxlength': 500,
        }),
        label='Tags',
        help_text='Add tags separated by commas',
    )

    class Meta:
        model = TimeEntry
        fields = [
            'task', 'start_time', 'end_time', 'description',
            'is_billable', 'billable_rate', 'currency'
        ]
        widgets = {
            'task': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'x-model': 'taskId',
                '@change': 'onTaskChange()',
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'datetime-local',
                'x-model': 'startTime',
                '@input': 'onStartTimeChange()',
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'datetime-local',
                'x-model': 'endTime',
                '@input': 'onEndTimeChange()',
                'x-bind:readonly': 'mode === "B"',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Describe what you worked on...',
                'rows': 3,
                'maxlength': 5000,
            }),
            'is_billable': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
                'x-model': 'isBillable',
            }),
            'billable_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '0.01',
                'min': '0',
                'x-show': 'isBillable',
                'x-model': 'billableRate',
                '@input': 'calculateRevenue()',
            }),
            'currency': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'x-show': 'isBillable',
            }),
        }
        labels = {
            'task': 'Task',
            'start_time': 'Start Time',
            'end_time': 'End Time',
            'description': 'Description',
            'is_billable': 'Billable',
            'billable_rate': 'Hourly Rate',
            'currency': 'Currency',
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        Initialize form with user context for task filtering and rate defaults.

        Args:
            user: User creating/editing the time entry
        """
        self.user = user
        super().__init__(*args, **kwargs)

        # Filter tasks to only user's accessible tasks
        if self.user:
            self.fields['task'].queryset = Task.objects.filter(
                task_list__workspace__owner=self.user
            ).select_related('task_list').order_by('title')

        # Make fields not required (handled by clean() method)
        self.fields['start_time'].required = False
        self.fields['end_time'].required = False
        self.fields['currency'].required = False  # Default will be set in clean()

        # Pre-populate tags_input with existing tags if editing
        if self.instance.pk:
            tag_names = [
                te_tag.tag.name
                for te_tag in self.instance.time_entry_tags.select_related('tag').all()
            ]
            if tag_names:
                self.fields['tags_input'].initial = ', '.join(tag_names)

            # Pre-populate duration_input if editing
            if self.instance.duration:
                hours = int(self.instance.duration.total_seconds() // 3600)
                minutes = int((self.instance.duration.total_seconds() % 3600) // 60)
                self.fields['duration_input'].initial = f"{hours}:{minutes:02d}"

        # Set default currency
        if not self.instance.pk:
            if self.user:
                try:
                    prefs = self.user.time_preferences
                    self.fields['currency'].initial = prefs.default_currency
                    # Pre-populate billable rate from user default
                    if prefs.default_billable_rate:
                        self.fields['billable_rate'].initial = prefs.default_billable_rate
                except UserTimePreferences.DoesNotExist:
                    self.fields['currency'].initial = 'USD'
            else:
                self.fields['currency'].initial = 'USD'

    def clean_duration_input(self):
        """
        Parse duration input from HH:MM or decimal hours format.

        Returns:
            timedelta: Parsed duration
        """
        duration_str = self.cleaned_data.get('duration_input', '').strip()

        if not duration_str:
            return None

        # Try parsing as HH:MM format
        if ':' in duration_str:
            try:
                parts = duration_str.split(':')
                if len(parts) != 2:
                    raise ValidationError('Duration must be in HH:MM format (e.g., 2:30)')

                hours = int(parts[0])
                minutes = int(parts[1])

                if hours < 0 or minutes < 0:
                    raise ValidationError('Duration cannot be negative.')
                if minutes >= 60:
                    raise ValidationError('Minutes must be less than 60.')

                return timedelta(hours=hours, minutes=minutes)

            except (ValueError, IndexError):
                raise ValidationError('Duration must be in HH:MM format (e.g., 2:30)')

        # Try parsing as decimal hours
        try:
            decimal_hours = float(duration_str)
            if decimal_hours < 0:
                raise ValidationError('Duration cannot be negative.')

            hours = int(decimal_hours)
            minutes = int((decimal_hours - hours) * 60)
            return timedelta(hours=hours, minutes=minutes)

        except ValueError:
            raise ValidationError('Duration must be in HH:MM format or decimal hours (e.g., 2.5)')

    def clean_tags_input(self):
        """
        Parse and validate comma-separated tag names.

        Returns:
            list: List of cleaned, deduplicated tag names
        """
        tags_input = self.cleaned_data.get('tags_input', '')

        if not tags_input or not tags_input.strip():
            return []

        # Split by comma and clean each tag name
        tag_names = [tag.strip().lower() for tag in tags_input.split(',')]

        # Remove empty tags
        tag_names = [tag for tag in tag_names if tag]

        # De-duplicate while preserving order
        seen = set()
        unique_tags = []
        for tag in tag_names:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        # Validate max 20 tags per entry
        if len(unique_tags) > 20:
            raise ValidationError('Maximum 20 tags allowed per time entry.')

        # Validate individual tag lengths
        for tag in unique_tags:
            if len(tag) > 50:
                raise ValidationError(f'Tag "{tag}" exceeds maximum length of 50 characters.')

        return unique_tags

    def clean(self):
        """
        Form-wide validation and mode detection.

        Implements three input modes:
        - Mode A: start_time + end_time → calculate duration
        - Mode B: start_time + duration → calculate end_time
        - Mode C: duration only → leave timestamps null

        Also applies time rounding rules from user preferences.
        """
        cleaned_data = super().clean()

        task = cleaned_data.get('task')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        duration_input = cleaned_data.get('duration_input')
        currency = cleaned_data.get('currency')

        # Task is required
        if not task:
            raise ValidationError({'task': 'Task is required.'})

        # Set default currency if not provided
        if not currency:
            if self.user:
                try:
                    prefs = self.user.time_preferences
                    cleaned_data['currency'] = prefs.default_currency
                except UserTimePreferences.DoesNotExist:
                    cleaned_data['currency'] = 'USD'
            else:
                cleaned_data['currency'] = 'USD'

        # Determine input mode and calculate missing field
        if start_time and end_time and not duration_input:
            # Mode A: Calculate duration from timestamps
            if end_time <= start_time:
                raise ValidationError({'end_time': 'End time must be after start time.'})

            duration = end_time - start_time
            cleaned_data['duration'] = duration

        elif start_time and duration_input and not end_time:
            # Mode B: Calculate end_time from start_time + duration
            end_time = start_time + duration_input
            cleaned_data['end_time'] = end_time
            cleaned_data['duration'] = duration_input

        elif duration_input and not start_time and not end_time:
            # Mode C: Duration only
            cleaned_data['start_time'] = None
            cleaned_data['end_time'] = None
            cleaned_data['duration'] = duration_input

        else:
            # Invalid combination
            raise ValidationError(
                'Please provide either: '
                '(1) Start Time and End Time, '
                '(2) Start Time and Duration, or '
                '(3) Duration only.'
            )

        # Validate duration is positive
        if cleaned_data.get('duration') and cleaned_data['duration'] <= timedelta(0):
            raise ValidationError({'duration': 'Duration must be positive.'})

        # Apply time rounding rules from user preferences
        if self.user and cleaned_data.get('duration'):
            try:
                prefs = self.user.time_preferences
                if prefs.rounding_interval > 0:
                    # Create temporary TimeEntry instance to use apply_rounding method
                    temp_entry = TimeEntry(duration=cleaned_data['duration'])
                    rounded_duration = temp_entry.apply_rounding(
                        prefs.rounding_interval,
                        prefs.rounding_method
                    )
                    cleaned_data['duration'] = rounded_duration

                    # Adjust end_time if in Mode A or B
                    if cleaned_data.get('start_time') and cleaned_data.get('end_time'):
                        # Recalculate end_time with rounded duration
                        cleaned_data['end_time'] = cleaned_data['start_time'] + rounded_duration

            except UserTimePreferences.DoesNotExist:
                # No preferences, skip rounding
                pass

        # Get billable rate from task/project hierarchy if not provided
        if cleaned_data.get('is_billable') and not cleaned_data.get('billable_rate'):
            if task:
                # Try task rate first
                if hasattr(task, 'default_billable_rate') and task.default_billable_rate:
                    cleaned_data['billable_rate'] = task.default_billable_rate
                # Then project rate
                elif hasattr(task.task_list, 'default_billable_rate') and task.task_list.default_billable_rate:
                    cleaned_data['billable_rate'] = task.task_list.default_billable_rate
                # Finally user default
                elif self.user:
                    try:
                        prefs = self.user.time_preferences
                        if prefs.default_billable_rate:
                            cleaned_data['billable_rate'] = prefs.default_billable_rate
                    except UserTimePreferences.DoesNotExist:
                        pass

        return cleaned_data

    def save(self, commit=True):
        """
        Save time entry and handle tags.

        Returns:
            TimeEntry: Saved time entry instance
        """
        instance = super().save(commit=False)

        # Set user
        if self.user:
            instance.user = self.user

        # Set duration from cleaned_data (calculated in clean() method)
        if 'duration' in self.cleaned_data:
            instance.duration = self.cleaned_data['duration']

        # Set start_time and end_time from cleaned_data
        if 'start_time' in self.cleaned_data:
            instance.start_time = self.cleaned_data['start_time']
        if 'end_time' in self.cleaned_data:
            instance.end_time = self.cleaned_data['end_time']

        # Inherit project from task
        if instance.task and not instance.project:
            instance.project = instance.task.task_list

        # Set is_running to False (manual entries are never running)
        instance.is_running = False

        if commit:
            instance.save()

            # Handle tags
            tag_names = self.cleaned_data.get('tags_input', [])
            if tag_names:
                # Clear existing tags
                TimeEntryTag.objects.filter(time_entry=instance).delete()

                # Get or create workspace for tags
                workspace = instance.task.task_list.workspace

                # Create new tags
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name,
                        workspace=workspace,
                        defaults={'created_by': self.user}
                    )
                    TimeEntryTag.objects.create(time_entry=instance, tag=tag)

        return instance


class UserTimePreferencesForm(forms.ModelForm):
    """
    Form for editing user time tracking preferences.

    Includes validation for time rounding, idle detection, Pomodoro timer,
    and billable rate settings.
    """

    class Meta:
        model = UserTimePreferences
        fields = [
            'rounding_interval',
            'rounding_method',
            'idle_threshold_minutes',
            'pomodoro_work_minutes',
            'pomodoro_break_minutes',
            'default_billable_rate',
            'default_currency',
        ]
        widgets = {
            'rounding_interval': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            }),
            'rounding_method': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            }),
            'idle_threshold_minutes': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'min': '1',
                'step': '1',
            }),
            'pomodoro_work_minutes': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'min': '5',
                'step': '1',
            }),
            'pomodoro_break_minutes': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'min': '1',
                'step': '1',
            }),
            'default_billable_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '0.01',
                'min': '0',
            }),
            'default_currency': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            }),
        }
        labels = {
            'rounding_interval': 'Time Rounding Interval',
            'rounding_method': 'Rounding Method',
            'idle_threshold_minutes': 'Idle Threshold (minutes)',
            'pomodoro_work_minutes': 'Pomodoro Work Duration (minutes)',
            'pomodoro_break_minutes': 'Pomodoro Break Duration (minutes)',
            'default_billable_rate': 'Default Billable Rate (per hour)',
            'default_currency': 'Default Currency',
        }
        help_texts = {
            'rounding_interval': 'Round time entries to the nearest interval (0 = no rounding)',
            'rounding_method': 'How to round time entries when rounding is enabled',
            'idle_threshold_minutes': 'Minutes of inactivity before idle detection triggers (minimum 1)',
            'pomodoro_work_minutes': 'Length of Pomodoro work interval (minimum 5 minutes)',
            'pomodoro_break_minutes': 'Length of Pomodoro break interval (minimum 1 minute)',
            'default_billable_rate': 'Default hourly rate for billable time entries (optional)',
            'default_currency': 'Default currency for billing',
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        Initialize form with user context.

        Args:
            user: User whose preferences are being edited
        """
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_idle_threshold_minutes(self):
        """Validate idle threshold is at least 1 minute."""
        value = self.cleaned_data.get('idle_threshold_minutes')
        if value is not None and value < 1:
            raise ValidationError('Idle threshold must be at least 1 minute.')
        return value

    def clean_pomodoro_work_minutes(self):
        """Validate Pomodoro work interval is at least 5 minutes."""
        value = self.cleaned_data.get('pomodoro_work_minutes')
        if value is not None and value < 5:
            raise ValidationError('Pomodoro work interval must be at least 5 minutes.')
        return value

    def clean_pomodoro_break_minutes(self):
        """Validate Pomodoro break interval is at least 1 minute."""
        value = self.cleaned_data.get('pomodoro_break_minutes')
        if value is not None and value < 1:
            raise ValidationError('Pomodoro break interval must be at least 1 minute.')
        return value

    def clean_default_billable_rate(self):
        """Validate billable rate is non-negative."""
        value = self.cleaned_data.get('default_billable_rate')
        if value is not None and value < 0:
            raise ValidationError('Billable rate cannot be negative.')
        return value

    def save(self, commit=True):
        """
        Save user preferences with get_or_create pattern.

        Returns:
            UserTimePreferences: Saved preferences instance
        """
        if not self.user:
            raise ValidationError('User is required to save preferences.')

        # Get or create preferences for this user
        instance, created = UserTimePreferences.objects.get_or_create(
            user=self.user,
            defaults={
                'rounding_interval': self.cleaned_data.get('rounding_interval', 0),
                'rounding_method': self.cleaned_data.get('rounding_method', 'nearest'),
                'idle_threshold_minutes': self.cleaned_data.get('idle_threshold_minutes', 5),
                'pomodoro_work_minutes': self.cleaned_data.get('pomodoro_work_minutes', 25),
                'pomodoro_break_minutes': self.cleaned_data.get('pomodoro_break_minutes', 5),
                'default_billable_rate': self.cleaned_data.get('default_billable_rate'),
                'default_currency': self.cleaned_data.get('default_currency', 'USD'),
            }
        )

        # Update existing instance with form data
        if not created:
            for field in self.Meta.fields:
                setattr(instance, field, self.cleaned_data.get(field))

        if commit:
            instance.save()

        return instance
