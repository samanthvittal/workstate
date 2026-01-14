"""
Django admin configuration for Task, TaskList, and Tag models.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Task, TaskList, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin interface for Tag model."""

    list_display = [
        'name',
        'get_colored_badge',
        'workspace',
        'created_by',
        'get_task_count',
        'created_at',
    ]

    list_filter = [
        'workspace',
        'created_at',
    ]

    search_fields = [
        'name',
        'workspace__name',
        'created_by__email',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'get_task_count',
    ]

    fieldsets = [
        ('Basic Information', {
            'fields': ('name', 'color')
        }),
        ('Organization', {
            'fields': ('workspace', 'created_by')
        }),
        ('Statistics', {
            'fields': ('get_task_count',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]

    list_per_page = 50

    def get_colored_badge(self, obj):
        """Display tag as a colored badge."""
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-size: 12px; font-weight: 500;">{}</span>',
            obj.color,
            obj.name
        )
    get_colored_badge.short_description = 'Tag Badge'

    def get_task_count(self, obj):
        """Display number of tasks using this tag."""
        return obj.tasks.count()
    get_task_count.short_description = 'Task Count'

    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('workspace', 'created_by').prefetch_related('tasks')


@admin.register(TaskList)
class TaskListAdmin(admin.ModelAdmin):
    """Admin interface for TaskList model."""

    list_display = [
        'name',
        'workspace',
        'created_by',
        'created_at',
    ]

    list_filter = [
        'workspace',
        'created_at',
    ]

    search_fields = [
        'name',
        'description',
        'workspace__name',
        'created_by__email',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
    ]

    fieldsets = [
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Organization', {
            'fields': ('workspace', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]

    list_per_page = 25

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('workspace', 'created_by')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for Task model."""

    list_display = [
        'title',
        'priority',
        'status',
        'due_date',
        'task_list',
        'get_workspace',
        'created_by',
        'created_at',
    ]

    list_filter = [
        'status',
        'priority',
        'task_list',
        'created_at',
    ]

    search_fields = [
        'title',
        'description',
        'created_by__email',
        'task_list__name',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'get_workspace',
    ]

    fieldsets = [
        ('Basic Information', {
            'fields': ('title', 'description', 'priority', 'status')
        }),
        ('Schedule', {
            'fields': ('due_date', 'due_time')
        }),
        ('Categorization', {
            'fields': ('tags',)
        }),
        ('Organization', {
            'fields': ('task_list', 'created_by', 'get_workspace')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]

    filter_horizontal = ['tags']  # Better UI for many-to-many field

    list_per_page = 25

    def get_workspace(self, obj):
        """Display workspace through task_list relationship."""
        return obj.workspace

    get_workspace.short_description = 'Workspace'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('task_list__workspace', 'created_by')
