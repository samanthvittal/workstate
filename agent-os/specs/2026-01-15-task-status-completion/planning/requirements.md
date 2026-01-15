# Requirements - Task Status & Completion (T008)

**Feature:** Enhanced status management with completion toggle, filtering, timestamps, and archive
**Spec Folder:** agent-os/specs/2026-01-15-task-status-completion
**Date:** January 15, 2026
**Priority:** P0 (High Priority - Core Functionality)

## User Requirements (Gathered from Q&A)

### 1. Completion Toggle Interaction
- **Method:** Click checkbox directly on task card for quick interaction
- **Keyboard Shortcuts:** Support 'x' or 'c' key to toggle completion
- **Scope:** Single task toggle (bulk operations out of scope)
- **Behavior:** HTMX-powered instant update without page refresh

### 2. Status Filtering
- **Location:** Toggle buttons in sidebar showing:
  - "Active" (default view)
  - "Completed"
  - "All" (both active and completed)
- **Persistence:** Save as user preference (persist across sessions)
- **Implementation:** Store in UserPreferences model or localStorage
- **Navigation:** Clear indication of active filter state

### 3. Completed Task Positioning
- **Behavior:** Automatically move to bottom of list when marked complete
- **Visual Distinction:**
  - Strikethrough on title
  - Moved to bottom of current list
- **Ordering:** Active tasks first (by creation date or custom order), completed tasks last

### 4. Completion Timestamps
- **Field:** Add `completed_at` datetime field to Task model
- **Capture:** Auto-captured on status change to 'completed'
- **Editability:** NOT editable (system-managed)
- **Display:**
  - On hover: "Completed 2 hours ago" (relative time)
  - In task details: "Completed on Jan 15, 2026 at 3:45 PM" (absolute time)
- **Reset:** Clear `completed_at` when task marked active again

### 5. "Mark All Complete" Bulk Action
- **Location:** Button appears when viewing a specific task list
- **Confirmation:** Requires confirmation dialog to prevent accidental clicks
- **Scope:** Marks all visible/filtered tasks in current list as complete
- **Excluded:** Does not affect already completed tasks
- **Success Message:** Toast notification with count (e.g., "5 tasks marked complete")

### 6. Archive Functionality
- **Implementation:** Soft delete with `is_archived=True` field
- **Database:** Tasks remain in database but hidden from normal views
- **Sidebar:** Separate "Archive" view accessible from sidebar
- **Behavior:**
  - Archived tasks only visible in Archive view
  - Can unarchive tasks (restore to active)
  - Archive button on completed tasks
  - Bulk archive action for all completed tasks
- **Counts:** Archived tasks excluded from all counts

### 7. Bulk Status Changes
- **Status:** OUT OF SCOPE for T008
- **Rationale:** Focused on single-task completion workflow
- **Future:** Consider for T013: Bulk Task Actions

### 8. Visual States for Completed Tasks
- **Strikethrough:** Title text has strikethrough style
- **Positioning:** Moved to bottom of list
- **Checkbox:** Filled/checked state
- **Simplicity:** Keep visual changes minimal and consistent with existing design
- **No:** Dimming, opacity changes, or completion badges (keep simple)

### 9. Sidebar Task Counts
- **Format:** Show both counts (e.g., "Today: 3 of 5 complete")
- **Components:**
  - First number: completed tasks
  - Second number: total tasks (active + completed)
- **Example:** "Overdue: 2 of 8 complete", "Upcoming: 5 of 12 complete"
- **Archive:** Archived tasks excluded from counts

### 10. Out of Scope Features
- ❌ Bulk status changes (multi-select tasks)
- ❌ Partial completion (50% done indicators)
- ❌ Status beyond active/completed (e.g., "in progress", "blocked")
- ❌ Recurring task handling on completion
- ❌ Editable completion timestamps

## Technical Requirements

### Database Changes (CRITICAL - Requires Migration)

**Task Model Updates:**
```python
class Task(models.Model):
    # Existing fields...
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # NEW FIELDS TO ADD:
    completed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    is_archived = models.BooleanField(default=False, db_index=True)
```

**Migration Steps:**
1. Add `completed_at` field (nullable, indexed for queries)
2. Add `is_archived` field (boolean, default=False, indexed)
3. Backfill `completed_at` for existing completed tasks (optional, use `updated_at`)

**UserPreferences Model Updates (if needed):**
```python
class UserPreferences(models.Model):
    # Existing fields...

    # NEW FIELD TO ADD:
    default_task_status_filter = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('completed', 'Completed'), ('all', 'All')],
        default='active'
    )
```

### Query Optimization (NO N+1 Queries)

**Task List View:**
```python
# Efficient query with proper ordering
tasks = Task.objects.filter(
    task_list=selected_tasklist,
    is_archived=False
).select_related(
    'created_by',
    'task_list',
    'task_list__workspace'
).prefetch_related(
    'tags'
).annotate(
    # Add sorting key: completed tasks go to bottom
    sort_order=Case(
        When(status='completed', then=Value(1)),
        default=Value(0),
        output_field=IntegerField()
    )
).order_by('sort_order', '-created_at')
```

**Sidebar Counts (Optimized):**
```python
# Single query with aggregation
counts = Task.objects.filter(
    task_list__workspace=current_workspace,
    is_archived=False
).aggregate(
    total_count=Count('id'),
    completed_count=Count('id', filter=Q(status='completed'))
)
# Format: "{completed_count} of {total_count} complete"
```

**Archive View:**
```python
# Separate query for archived tasks
archived_tasks = Task.objects.filter(
    task_list__workspace=current_workspace,
    is_archived=True
).select_related('created_by', 'task_list').prefetch_related('tags').order_by('-completed_at')
```

### Existing Code to Leverage

**Models:**
- `tasks/models.py` - Task model with status field (extend with completed_at, is_archived)
- `accounts/models.py` - UserPreferences model (add default_task_status_filter)

**Views:**
- `tasks/views.py` - TaskListView (add status filtering)
- `tasks/views.py` - TaskUpdateView (handle completion toggle)

**Templates:**
- `templates/tasks/_task_card.html` - Task card component (make checkbox interactive)
- `templates/includes/dashboard_sidebar.html` - Sidebar (add status filter buttons, archive link)

**Components:**
- HTMX patterns for dynamic updates (task cards already use HTMX)
- Alpine.js for keyboard shortcuts (add event listener)
- Tailwind CSS for styling (use existing utility classes)

**URLs:**
- Add: `tasks/<int:pk>/toggle-status/` (HTMX endpoint)
- Add: `tasks/<int:pk>/archive/` (archive single task)
- Add: `tasklist/<int:pk>/mark-all-complete/` (bulk action)
- Add: `tasks/archived/` (archive view)

### User Interface Components

**Status Filter Buttons (Sidebar):**
```html
<div class="flex gap-2 mb-4">
  <button class="px-3 py-1 rounded {% if filter == 'active' %}bg-blue-600 text-white{% else %}bg-gray-100{% endif %}">
    Active
  </button>
  <button class="px-3 py-1 rounded {% if filter == 'completed' %}bg-blue-600 text-white{% else %}bg-gray-100{% endif %}">
    Completed
  </button>
  <button class="px-3 py-1 rounded {% if filter == 'all' %}bg-blue-600 text-white{% else %}bg-gray-100{% endif %}">
    All
  </button>
</div>
```

**Interactive Checkbox:**
```html
<input type="checkbox"
       {% if task.status == 'completed' %}checked{% endif %}
       hx-post="{% url 'tasks:toggle-status' pk=task.id %}"
       hx-target="#task-{{ task.id }}"
       hx-swap="outerHTML"
       class="h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer">
```

**Completed Task Visual:**
```html
<a href="{% url 'tasks:task-detail' pk=task.id %}"
   class="text-lg font-medium hover:text-blue-600
          {% if task.status == 'completed' %}line-through text-gray-500{% else %}text-gray-900{% endif %}">
    {{ task.title }}
</a>
```

**Mark All Complete Button:**
```html
<button hx-post="{% url 'tasks:mark-all-complete' pk=task_list.id %}"
        hx-confirm="Mark all tasks in this list as complete?"
        class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
    Mark All Complete
</button>
```

**Archive Link (Sidebar):**
```html
<a href="{% url 'tasks:archived' %}"
   class="flex items-center gap-2 px-3 py-2 text-gray-700 hover:bg-gray-50 rounded-md">
    <svg class="w-5 h-5"><!-- archive icon --></svg>
    Archive
</a>
```

**Keyboard Shortcuts (Alpine.js):**
```html
<div x-data @keydown.window.prevent.x="toggleCompletion($event)"
              @keydown.window.prevent.c="toggleCompletion($event)">
    <!-- Task list content -->
</div>
```

## Success Criteria

- ✅ Users can toggle task completion by clicking checkbox
- ✅ Users can use 'x' or 'c' keyboard shortcut to toggle completion
- ✅ Status filter persists across sessions (user preference)
- ✅ Completed tasks move to bottom of list automatically
- ✅ Completion timestamp captured and displayed
- ✅ "Mark all complete" requires confirmation dialog
- ✅ Archive view accessible from sidebar
- ✅ Archived tasks hidden from normal views
- ✅ Sidebar counts show "X of Y complete" format
- ✅ NO N+1 queries (use .select_related(), .prefetch_related(), .annotate())
- ✅ Database migration created and applied successfully
- ✅ 12-15 tests pass (cover all major workflows)
- ✅ Responsive design on all devices

## Implementation Priority

**P0 (High Priority for MVP)**
- Estimated Time: 4-6 hours
- Complexity: Low
- Impact: High (completes core task lifecycle)
- Dependencies: None

## Visual Assets

- No mockups provided
- Keep UI simple and consistent with existing design
- Reuse existing components and patterns

## Related Features

- **T001-T006:** Core Task CRUD (foundation)
- **T007:** Task Labels & Tags (completed)
- **T010:** Task Due Date Management (completed)
- **T013:** Bulk Task Actions (future, excludes bulk status changes)
