"""
Forms for task creation and editing.
"""
from django import forms
from django.core.exceptions import ValidationError
from tasks.models import Task, TaskList, Tag


class TaskForm(forms.ModelForm):
    """
    Form for creating and editing tasks.
    Includes validation for title, description, due dates, priority, status, and tags.
    """

    # Custom field for tag input (comma-separated tag names)
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., work, urgent, client-a',
            'maxlength': 500,
        }),
        label='Tags',
        help_text='Add tags separated by commas (e.g., work, urgent, personal)',
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'due_time', 'priority', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter task title',
                'autofocus': True,
                'maxlength': 255,
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Add task details (supports markdown)',
                'rows': 5,
                'maxlength': 10000,
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'date',
                'x-ref': 'due_date',
            }),
            'due_time': forms.TimeInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'time',
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            }),
        }
        labels = {
            'title': 'What needs to be done?',
            'description': 'Description',
            'due_date': 'When is this due?',
            'due_time': 'Specific deadline time (optional)',
            'priority': 'How urgent is this task?',
            'status': 'Status',
        }
        help_texts = {
            'title': 'Task title (max 255 characters)',
            'description': 'Add details (supports markdown)',
            'due_date': 'When is this due?',
            'due_time': 'Specific deadline time (optional)',
            'priority': 'How urgent is this task?',
        }

    def __init__(self, *args, **kwargs):
        """Initialize form and set status field as not required."""
        super().__init__(*args, **kwargs)
        # Status field should not be required (defaults to 'active' in model)
        self.fields['status'].required = False
        # Set initial value for status if creating a new task
        if not self.instance.pk:
            self.fields['status'].initial = 'active'

        # Pre-populate tags_input with existing tags if editing
        if self.instance.pk and self.instance.tags.exists():
            tag_names = [tag.name for tag in self.instance.tags.all()]
            self.fields['tags_input'].initial = ', '.join(tag_names)

    def clean_title(self):
        """
        Validate title field.
        Strip whitespace and ensure not empty.
        """
        title = self.cleaned_data.get('title')

        if title:
            # Strip whitespace from both ends
            title = title.strip()

            # Ensure title is not empty after stripping
            if not title:
                raise ValidationError('Title cannot be empty or only whitespace.')

        return title

    def clean_description(self):
        """
        Validate description field.
        Ensure max length of 10,000 characters.
        """
        description = self.cleaned_data.get('description', '')

        if description and len(description) > 10000:
            raise ValidationError('Description must be no more than 10,000 characters.')

        return description

    def clean_tags_input(self):
        """
        Parse and validate comma-separated tag names.
        Returns a list of cleaned, deduplicated tag names.
        """
        tags_input = self.cleaned_data.get('tags_input', '')

        # Return empty list if no tags provided
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

        # Validate max 20 tags per task
        if len(unique_tags) > 20:
            raise ValidationError('Maximum 20 tags allowed per task.')

        # Validate individual tag lengths
        for tag in unique_tags:
            if len(tag) > 50:
                raise ValidationError(f'Tag "{tag}" exceeds maximum length of 50 characters.')

        return unique_tags

    def clean(self):
        """
        Form-wide validation.
        Validate that due_time requires due_date and priority is valid.
        """
        cleaned_data = super().clean()
        due_date = cleaned_data.get('due_date')
        due_time = cleaned_data.get('due_time')
        priority = cleaned_data.get('priority')

        # Validate due_time requires due_date
        if due_time and not due_date:
            raise ValidationError({
                'due_time': 'Cannot set due time without a due date.'
            })

        # Validate priority is one of P1/P2/P3/P4
        valid_priorities = ['P1', 'P2', 'P3', 'P4']
        if priority and priority not in valid_priorities:
            raise ValidationError({
                'priority': 'Priority must be one of P1 (Urgent), P2 (High), P3 (Medium), or P4 (Low).'
            })

        return cleaned_data


class TaskListForm(forms.ModelForm):
    """
    Form for creating and editing task lists.
    """

    class Meta:
        model = TaskList
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter task list name',
                'autofocus': True,
                'maxlength': 255,
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Add task list description (optional)',
                'rows': 3,
            }),
        }
        labels = {
            'name': 'Task List Name',
            'description': 'Description (optional)',
        }
        help_texts = {
            'name': 'What is this task list for? (e.g., "Personal", "Work Projects", "Client A")',
            'description': 'Add more details about this task list',
        }

    def clean_name(self):
        """
        Validate name field.
        Strip whitespace and ensure not empty.
        """
        name = self.cleaned_data.get('name')

        if name:
            # Strip whitespace from both ends
            name = name.strip()

            # Ensure name is not empty after stripping
            if not name:
                raise ValidationError('Name cannot be empty or only whitespace.')

        return name
