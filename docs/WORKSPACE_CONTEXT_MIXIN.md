# WorkspaceContextMixin Documentation

## Overview

`WorkspaceContextMixin` is a reusable Django mixin that provides consistent workspace and task list context to all views across the application. It centralizes workspace context logic in a single location, following the DRY (Don't Repeat Yourself) principle.

**Location:** `accounts/mixins.py`

**Created:** January 2026 to fix missing task lists in Time Tracking sidebar

## Purpose

The sidebar template (`templates/includes/dashboard_sidebar.html`) requires specific context variables to display workspace information and task lists. Without these variables, the sidebar shows "No workspace selected" or "No task lists yet" even when data exists.

This mixin ensures **every view** that uses the dashboard layout has access to:
- User's workspaces
- Currently selected workspace
- Task lists for the current workspace (with task counts)
- Currently selected task list (optional)

## Benefits

1. **DRY Principle** - Workspace context logic defined once, reused everywhere
2. **Consistency** - All views get the same workspace context with identical behavior
3. **Maintainability** - Changes to workspace logic only need updating in one place
4. **Testability** - Mixin can be tested independently of views
5. **Reusability** - Future views can inherit the mixin easily
6. **Query Optimization** - Uses optimized queries with annotations (2-4 queries total)
7. **Error Handling** - Gracefully handles edge cases (no workspaces, invalid IDs)

## Context Variables Provided

The mixin adds these variables to the template context:

| Variable | Type | Description |
|----------|------|-------------|
| `workspaces` | QuerySet | All workspaces owned by the current user |
| `current_workspace` | Workspace or None | Currently selected workspace (from URL or first workspace) |
| `task_lists` | QuerySet | Task lists for current workspace with `.active_count` and `.completed_count` annotations |
| `selected_tasklist` | TaskList or None | Currently selected task list from URL parameter (optional) |

## Usage

### Basic Usage (Generic Views)

For Django generic views (TemplateView, FormView, etc.), simply add the mixin to your class inheritance:

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from accounts.mixins import WorkspaceContextMixin

class MyView(LoginRequiredMixin, WorkspaceContextMixin, TemplateView):
    template_name = 'my_template.html'

    # Workspace context automatically available in template
    # No additional code needed!
```

The mixin automatically provides workspace context through the `get_context_data()` method.

### Usage with Custom Views (View class)

For custom views using Django's base `View` class, manually call the mixin's method:

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from accounts.mixins import WorkspaceContextMixin

class MyCustomView(LoginRequiredMixin, WorkspaceContextMixin, View):
    def get(self, request):
        # Get workspace context from mixin
        workspace_context = self.get_workspace_context(request)

        # Build your view-specific context
        context = {
            **workspace_context,  # Spread workspace context
            'my_data': some_data,
            'my_other_data': other_data,
        }

        return render(request, 'my_template.html', context)
```

### Usage in POST Handlers

If your view needs workspace context in POST handlers (e.g., for error pages), call the mixin method:

```python
def post(self, request):
    # Get workspace context from mixin
    workspace_context = self.get_workspace_context(request)

    form = MyForm(data=request.POST)

    if form.is_valid():
        # Handle valid form
        pass

    # Re-render form with errors and workspace context
    context = {
        **workspace_context,  # Include workspace context
        'form': form,
    }

    return render(request, 'my_template.html', context)
```

## URL Parameters

The mixin respects these query parameters:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `workspace` | int | Workspace ID to select | `?workspace=5` |
| `tasklist` | int | Task list ID to select | `?tasklist=12` |

**Default Behavior:**
- If no `workspace` parameter is provided, the first workspace is selected
- If no `tasklist` parameter is provided, no task list is selected
- Invalid workspace IDs return 404 (security)
- Invalid tasklist IDs are gracefully ignored (no crash)

## Query Optimization

The mixin uses optimized database queries to prevent N+1 problems:

### Query Count: 2-4 queries per request

1. **Query 1:** Get all user's workspaces
   ```python
   workspaces = request.user.workspaces.all()
   ```

2. **Query 2:** Get current workspace (conditional, only if workspace param provided)
   ```python
   current_workspace = get_object_or_404(Workspace, id=workspace_id, owner=request.user)
   ```

3. **Query 3:** Get task lists with annotated counts (single query with Count aggregations)
   ```python
   task_lists = TaskList.objects.filter(
       workspace=current_workspace
   ).annotate(
       active_count=Count('tasks', filter=Q(tasks__status='active', tasks__is_archived=False)),
       completed_count=Count('tasks', filter=Q(tasks__status='completed', tasks__is_archived=False))
   ).order_by('-created_at')
   ```

4. **Query 4:** Get selected task list (conditional, only if tasklist param provided)
   ```python
   selected_tasklist = task_lists.get(id=tasklist_id)
   ```

**Performance:** 2-4 queries is well within acceptable limits for Django views. The annotations prevent additional queries when templates access `.active_count` and `.completed_count`.

## Edge Cases and Error Handling

The mixin handles these edge cases gracefully:

| Edge Case | Behavior |
|-----------|----------|
| User has no workspaces | `current_workspace = None`, `task_lists = TaskList.objects.none()` |
| Invalid workspace ID in URL | Returns 404 (via `get_object_or_404`) |
| Invalid tasklist ID in URL | `selected_tasklist = None` (gracefully ignored) |
| Workspace with no task lists | `task_lists = []` (empty queryset, safe for templates) |
| No workspace parameter | Defaults to first workspace |
| No tasklist parameter | `selected_tasklist = None` |

**Security:** The mixin validates workspace ownership using `get_object_or_404`, preventing users from accessing workspaces they don't own.

## Template Usage

In your templates, access the workspace context variables:

```django
{% if current_workspace %}
  <h2>{{ current_workspace.name }}</h2>

  {% if task_lists %}
    <ul>
      {% for tasklist in task_lists %}
        <li>
          {{ tasklist.name }}
          <span class="badge">{{ tasklist.active_count }} active</span>
          <span class="badge">{{ tasklist.completed_count }} completed</span>
        </li>
      {% endfor %}
    </ul>
  {% else %}
    <p>No task lists yet.</p>
  {% endif %}
{% else %}
  <p>No workspace selected.</p>
{% endif %}
```

## Real-World Examples

### Example 1: Time Entry List View

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from accounts.mixins import WorkspaceContextMixin

class TimeEntryListHTMLView(LoginRequiredMixin, WorkspaceContextMixin, View):
    def get(self, request):
        # Get workspace context from mixin
        workspace_context = self.get_workspace_context(request)

        # Build time entry specific context
        entries = TimeEntry.objects.filter(user=request.user)

        context = {
            **workspace_context,  # Spread workspace context from mixin
            'entries': entries,
            'grand_total': calculate_total(entries),
        }

        return render(request, 'time_tracking/time_entry_list.html', context)
```

### Example 2: Analytics Dashboard

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from accounts.mixins import WorkspaceContextMixin

class AnalyticsDashboardView(LoginRequiredMixin, WorkspaceContextMixin, View):
    def get(self, request):
        try:
            # Get workspace context from mixin
            workspace_context = self.get_workspace_context(request)

            # Calculate analytics
            summary = calculate_summary(request.user)

            context = {
                **workspace_context,  # Spread workspace context from mixin
                'summary': summary,
                'charts': generate_charts(request.user),
            }

            return render(request, 'time_tracking/analytics_dashboard.html', context)

        except Exception as e:
            # Even error pages need workspace context for sidebar
            workspace_context = self.get_workspace_context(request)

            context = {
                **workspace_context,
                'error_message': 'An error occurred.',
            }

            return render(request, 'time_tracking/analytics_dashboard.html', context)
```

### Example 3: Settings Page (FormView)

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView
from accounts.mixins import WorkspaceContextMixin

class TimeTrackingSettingsView(LoginRequiredMixin, WorkspaceContextMixin, FormView):
    template_name = 'time_tracking/settings.html'
    form_class = UserTimePreferencesForm

    def get_context_data(self, **kwargs):
        # WorkspaceContextMixin automatically adds workspace context via super()
        context = super().get_context_data(**kwargs)

        # Add view-specific context
        context['page_title'] = 'Time Tracking Settings'

        return context
```

## Troubleshooting

### Problem: Sidebar still shows "No task lists yet"

**Solution:** Verify these steps:

1. Check that your view inherits from `WorkspaceContextMixin`:
   ```python
   class MyView(LoginRequiredMixin, WorkspaceContextMixin, View):
   ```

2. For custom views, ensure you're calling `get_workspace_context()`:
   ```python
   workspace_context = self.get_workspace_context(request)
   ```

3. For generic views, ensure you're calling `super().get_context_data()`:
   ```python
   def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)  # This adds workspace context
       return context
   ```

4. Verify you're spreading the workspace context into your context dict:
   ```python
   context = {
       **workspace_context,  # Don't forget this!
       'my_data': data,
   }
   ```

### Problem: 404 error when accessing view

**Cause:** Invalid workspace ID in URL parameter

**Solution:** The mixin validates workspace ownership. If a user tries to access a workspace they don't own, `get_object_or_404` raises a 404. This is expected security behavior.

### Problem: Template error "object has no attribute 'active_count'"

**Cause:** Task lists were fetched without annotations

**Solution:** Don't override the mixin's `task_lists` in your view. The mixin already provides annotated task lists. If you need to filter task lists, filter the `task_lists` from the mixin:

```python
# WRONG - loses annotations
task_lists = TaskList.objects.filter(workspace=current_workspace)

# CORRECT - use mixin's annotated queryset
workspace_context = self.get_workspace_context(request)
filtered_task_lists = workspace_context['task_lists'].filter(name__icontains='search')
```

### Problem: Too many database queries

**Cause:** Template accessing related objects without `select_related` or `prefetch_related`

**Solution:** The mixin already optimizes its queries. If you're seeing N+1 queries, they're likely from your view-specific code, not the mixin.

## Testing

When writing tests for views that use `WorkspaceContextMixin`, create test workspaces and task lists:

```python
import pytest
from django.test import RequestFactory
from accounts.models import Workspace
from tasks.models import TaskList

@pytest.mark.django_db
def test_my_view_with_workspace_context():
    # Setup
    user = create_test_user()
    workspace = Workspace.objects.create(name='Test Workspace', owner=user)
    task_list = TaskList.objects.create(name='Test List', workspace=workspace)

    # Create request
    factory = RequestFactory()
    request = factory.get('/my-view/')
    request.user = user

    # Test view
    response = MyView.as_view()(request)

    # Assertions
    assert response.status_code == 200
    assert 'current_workspace' in response.context_data
    assert 'task_lists' in response.context_data
```

## Migration Guide

If you have existing views that manually retrieve workspace context, follow these steps to migrate:

### Step 1: Add the import

```python
from accounts.mixins import WorkspaceContextMixin
```

### Step 2: Add mixin to class inheritance

**Before:**
```python
class MyView(LoginRequiredMixin, View):
```

**After:**
```python
class MyView(LoginRequiredMixin, WorkspaceContextMixin, View):
```

### Step 3: Remove duplicate workspace context code

**Before:**
```python
def get(self, request):
    # Get workspaces
    workspaces = request.user.workspaces.all()

    # Get current workspace
    workspace_id = request.GET.get('workspace')
    if workspace_id:
        current_workspace = get_object_or_404(Workspace, id=workspace_id, owner=request.user)
    else:
        current_workspace = workspaces.first()

    # ... rest of view logic ...

    context = {
        'workspaces': workspaces,
        'current_workspace': current_workspace,
        'my_data': data,
    }
```

**After:**
```python
def get(self, request):
    # Get workspace context from mixin
    workspace_context = self.get_workspace_context(request)

    # ... rest of view logic ...

    context = {
        **workspace_context,  # Spread workspace context from mixin
        'my_data': data,
    }
```

### Step 4: Update error handlers

Ensure error handlers also use the mixin:

```python
except Exception as e:
    workspace_context = self.get_workspace_context(request)
    context = {
        **workspace_context,
        'error_message': 'An error occurred.',
    }
    return render(request, 'my_template.html', context)
```

## Related Patterns

### Similar Mixins in Codebase

- **WorkspaceAccessMixin** (`accounts/mixins.py`) - Validates workspace access permissions
- **TaskListAccessMixin** (`tasks/mixins.py`) - Validates task list access permissions

These mixins focus on **permission checking**, while `WorkspaceContextMixin` focuses on **providing context data**.

### When to Use Each Mixin

| Mixin | Purpose | When to Use |
|-------|---------|-------------|
| WorkspaceContextMixin | Provides workspace/task list context for templates | When sidebar needs workspace/task list display |
| WorkspaceAccessMixin | Validates user has access to workspace | When view operates on specific workspace |
| TaskListAccessMixin | Validates user has access to task list | When view operates on specific task list |

**You can use multiple mixins together:**

```python
class MyView(LoginRequiredMixin, WorkspaceContextMixin, WorkspaceAccessMixin, View):
    # Provides workspace context AND validates access
    pass
```

## Best Practices

1. **Always inherit from LoginRequiredMixin first** - Ensures user is authenticated before accessing workspace data
2. **Use spread operator (`**dict`)** - Cleanly merge workspace context with view context
3. **Call mixin method in error handlers** - Ensure error pages have workspace context for sidebar
4. **Don't override task_lists without annotations** - Use the mixin's annotated queryset
5. **Test edge cases** - No workspaces, invalid IDs, empty task lists
6. **Document view inheritance** - Make it clear which mixins a view uses

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-16 | Initial creation of WorkspaceContextMixin | Claude Code |
| 2026-01-16 | Applied to all Time Tracking views | Claude Code |

## Future Enhancements

Potential improvements to consider:

1. **Caching** - Cache workspace context for duration of request to avoid duplicate queries
2. **Prefetching** - Add `prefetch_related` for tags or other related objects
3. **Custom ordering** - Allow views to specify custom task list ordering
4. **Filtering** - Add optional parameters for filtering task lists (archived, active, etc.)

## Support

If you encounter issues with `WorkspaceContextMixin`, check:

1. This documentation
2. Implementation in `accounts/mixins.py`
3. Example usage in `time_tracking/views/` directory
4. Unit tests (when available)

For questions or issues, refer to the project's issue tracker or documentation.
