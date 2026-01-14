"""
Django admin configuration for Task and TaskList models.
"""
from django.contrib import admin
from .models import Task, TaskList


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
        ('Organization', {
            'fields': ('task_list', 'created_by', 'get_workspace')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]

    list_per_page = 25

    def get_workspace(self, obj):
        """Display workspace through task_list relationship."""
        return obj.workspace

    get_workspace.short_description = 'Workspace'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('task_list__workspace', 'created_by')
