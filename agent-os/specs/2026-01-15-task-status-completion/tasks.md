# Task Breakdown: Task Status & Completion

## Overview

**Feature:** Task Status & Completion (T008)
**Total Tasks:** 5 task groups with 30 sub-tasks
**Priority:** P0 (High Priority - Core Functionality)
**Estimated Time:** 4-6 hours
**Target Test Count:** 12-15 tests maximum

This feature completes the core task lifecycle by enabling interactive completion toggles, status filtering with persistent user preferences, automatic positioning of completed tasks, completion timestamp tracking, bulk actions, and archive functionality.

## Task List

### Database Layer

#### Task Group 1: Database Schema & Migrations
**Dependencies:** None

- [x] 1.0 Complete database schema updates and migrations
  - [x] 1.1 Write 2-4 focused tests for model enhancements
    - Test `completed_at` is set when marking task complete
    - Test `completed_at` is cleared when marking task active
    - Test `is_archived=True` excludes task from active queries
    - Test database constraint ensures `completed_at` only set when `status='completed'`
    - Limit to maximum 4 tests covering critical model behaviors only
  - [x] 1.2 Add new fields to Task model (`tasks/models.py`)
    - Add `completed_at = models.DateTimeField(null=True, blank=True, db_index=True)`
    - Add `is_archived = models.BooleanField(default=False, db_index=True)`
    - Add composite index on `(task_list, status, is_archived)` in Meta class
    - Add CheckConstraint to ensure `completed_at` only set when `status='completed'`
    - Follow existing timestamp pattern from `created_at` and `updated_at` fields
  - [x] 1.3 Extend Task model methods
    - Update `mark_complete()` method to set `completed_at=timezone.now()`
    - Update `mark_active()` method to clear `completed_at=None`
    - Add `archive()` method to set `is_archived=True`
    - Add `unarchive()` method to set `is_archived=False`
    - Follow existing method pattern from lines 455-460
  - [x] 1.4 Add UserPreferences field for filter persistence
    - Add `default_task_status_filter` field to UserPreferences model (`accounts/models.py`)
    - CharField with max_length=20, choices=[('active', 'Active'), ('completed', 'Completed'), ('all', 'All')]
    - Set default='active' for new users
    - Follow existing CharField pattern from lines 160-177
  - [x] 1.5 Create database migration
    - Run `python manage.py makemigrations` to create migration file
    - Add data migration step to backfill `completed_at` for existing completed tasks (use `updated_at` value)
    - Verify migration SQL is safe (no data loss)
    - Run `python manage.py migrate` to apply changes
  - [x] 1.6 Ensure database layer tests pass
    - Run ONLY the 2-4 tests written in 1.1
    - Verify migrations run successfully
    - Verify new fields work correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-4 tests written in 1.1 pass
- Task model has `completed_at` and `is_archived` fields with proper indexes
- UserPreferences model has `default_task_status_filter` field
- Database constraint ensures data integrity
- Migration applies cleanly with backfill for existing data
- Model methods correctly manage `completed_at` timestamps

---

### Backend Views Layer

#### Task Group 2: Status Toggle & Filtering Views
**Dependencies:** Task Group 1

- [x] 2.0 Complete status toggle and filtering logic
  - [x] 2.1 Write 2-4 focused tests for view behaviors
    - Test `TaskToggleStatusView` flips task status correctly
    - Test `TaskToggleStatusView` updates `completed_at` timestamp
    - Test status filter query parameter filters tasks correctly
    - Test status filter persists to UserPreferences
    - Limit to maximum 4 tests covering critical view logic only
  - [x] 2.2 Create TaskToggleStatusView (`tasks/views.py`)
    - Inherit from `LoginRequiredMixin`, `View`
    - Handle POST request to toggle task status
    - Use `task.mark_complete()` or `task.mark_active()` based on current status
    - Return updated task card partial HTML using `_task_card.html` template
    - Use `select_related('task_list__workspace', 'created_by')` for query optimization
    - Verify user owns workspace containing task before toggling
    - Return 403 if permission check fails
  - [x] 2.3 Extend TaskListView filtering (`tasks/views.py`)
    - Update `get_queryset()` to handle status filter from query parameter
    - Add `?status=active|completed|all` support (default to user preference)
    - Always exclude archived tasks: `.filter(is_archived=False)`
    - Load user's `default_task_status_filter` from `request.user.preferences`
    - Apply status filter using `Q()` objects for complex conditions
    - Reuse existing workspace and tag filtering logic
  - [x] 2.4 Add completed task positioning logic
    - Use `.annotate()` with `Case/When` to add `sort_order` field
    - `sort_order=1` for completed tasks, `sort_order=0` for active tasks
    - Order by `sort_order` first, then `created_at` descending
    - Apply ordering in all task list contexts (dashboard, task list detail)
    - Follow query optimization pattern with `select_related()` and `prefetch_related()`
  - [x] 2.5 Update user preference on filter change
    - Detect when user changes status filter via query parameter
    - Update `request.user.preferences.default_task_status_filter` field
    - Save preference change to database
    - Handle case where user doesn't have UserPreference object yet
  - [x] 2.6 Add context data for UI state
    - Add `current_status_filter` to context (active/completed/all)
    - Add `filter_counts` dict with counts for each filter option
    - Use `.aggregate()` for efficient count queries (no N+1)
    - Pass context to template for rendering filter buttons
  - [x] 2.7 Ensure view layer tests pass
    - Run ONLY the 2-4 tests written in 2.1
    - Verify TaskToggleStatusView works correctly
    - Verify status filtering works correctly
    - Verify user preference persistence works
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-4 tests written in 2.1 pass ✅
- TaskToggleStatusView successfully toggles task status ✅
- Status filter query parameter filters tasks correctly (active/completed/all) ✅
- User preference persists across sessions ✅
- Completed tasks automatically move to bottom of list ✅
- NO N+1 queries (verified with Django Debug Toolbar or query logging) ✅

---

### Bulk Actions & Archive Layer

#### Task Group 3: Bulk Complete & Archive Functionality
**Dependencies:** Task Group 2

- [x] 3.0 Complete bulk actions and archive functionality
  - [x] 3.1 Write 2-4 focused tests for bulk operations
    - Test `TaskListMarkAllCompleteView` marks all active tasks complete
    - Test bulk complete sets `completed_at` timestamp for all tasks
    - Test `TaskArchiveView` sets `is_archived=True` without deleting
    - Test `ArchivedTaskListView` shows only archived tasks
    - Limit to maximum 4 tests covering critical bulk behaviors only
  - [x] 3.2 Create TaskListMarkAllCompleteView (`tasks/views.py`)
    - Inherit from `LoginRequiredMixin`, `View`
    - Handle POST request to mark all active tasks complete in a task list
    - Filter tasks: `task_list_id=pk`, `status='active'`, `is_archived=False`
    - Use transaction for data consistency: `from django.db import transaction`
    - Use `.update()` for bulk operation: `tasks.update(status='completed', completed_at=timezone.now())`
    - Return success message with count via Django messages framework
    - Add HX-Trigger header to refresh task list: `response['HX-Trigger'] = 'taskListRefresh'`
    - Verify user owns workspace before performing bulk action
  - [x] 3.3 Create TaskArchiveView (`tasks/views.py`)
    - Inherit from `LoginRequiredMixin`, `View`
    - Handle POST request to archive single task
    - Set `task.is_archived=True` using `.update()` method
    - Keep all other data intact (soft delete pattern)
    - Return success message via Django messages
    - Add HX-Trigger header to remove task from list
    - Verify user owns workspace before archiving
  - [x] 3.4 Create TaskListArchiveAllCompletedView (`tasks/views.py`)
    - Inherit from `LoginRequiredMixin`, `View`
    - Handle POST request to bulk archive all completed tasks in a task list
    - Filter tasks: `task_list_id=pk`, `status='completed'`, `is_archived=False`
    - Use transaction for data consistency
    - Use `.update()` for bulk operation: `tasks.update(is_archived=True)`
    - Return success message with archived task count
    - Add HX-Trigger header to refresh task list
    - Verify user owns workspace before performing bulk action
  - [x] 3.5 Create ArchivedTaskListView (`tasks/views.py`)
    - Inherit from `LoginRequiredMixin`, `ListView`
    - Filter tasks: `is_archived=True`, workspace owned by user
    - Order by `completed_at` descending (most recently completed first)
    - Use `select_related()` and `prefetch_related()` for query optimization
    - Template: `tasks/archived_task_list.html`
    - Add context data for unarchive button display
  - [x] 3.6 Add URL patterns for bulk actions (`tasks/urls.py`)
    - `path('tasklist/<int:pk>/mark-all-complete/', TaskListMarkAllCompleteView.as_view(), name='mark-all-complete')`
    - `path('tasks/<int:pk>/archive/', TaskArchiveView.as_view(), name='archive-task')`
    - `path('tasklist/<int:pk>/archive-all-completed/', TaskListArchiveAllCompletedView.as_view(), name='archive-all-completed')`
    - `path('tasks/archived/', ArchivedTaskListView.as_view(), name='archived-tasks')`
    - Follow existing URL naming convention
  - [x] 3.7 Ensure bulk action and archive tests pass
    - Run ONLY the 2-4 tests written in 3.1
    - Verify bulk complete updates all tasks in transaction
    - Verify archive functionality works correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-4 tests written in 3.1 pass ✅
- "Mark All Complete" marks all active tasks with confirmation ✅
- Bulk operations use transactions for data consistency ✅
- Archive functionality soft-deletes tasks (sets `is_archived=True`) ✅
- Archived tasks view shows only archived tasks ✅
- URL routing works correctly for all bulk actions ✅
- Permission checks enforce workspace ownership ✅

---

### Frontend Templates & UI Layer

#### Task Group 4: Interactive UI Components & HTMX Integration
**Dependencies:** Task Groups 1-3

- [x] 4.0 Complete frontend templates and interactivity
  - [x] 4.1 Write 2-4 focused tests for UI rendering
    - Test interactive checkbox renders with HTMX attributes
    - Test status filter buttons display with active state styling
    - Test completed task visual styling (strikethrough, color)
    - Test sidebar counts display in "X of Y complete" format
    - Limit to maximum 4 tests covering critical UI behaviors only
  - [x] 4.2 Update task card template with interactive checkbox (`templates/tasks/_task_card.html`)
    - Replace disabled checkbox (line 12) with interactive HTMX checkbox
    - Add `hx-post="{% url 'tasks:toggle-status' pk=task.id %}"`
    - Add `hx-target="#task-{{ task.id }}"` and `hx-swap="outerHTML"`
    - Use checked state: `{% if task.status == 'completed' %}checked{% endif %}`
    - Add cursor-pointer class for visual feedback
    - Wrap task card in `<div id="task-{{ task.id }}"...>` for HTMX targeting
  - [x] 4.3 Add completed task visual styling to task card
    - Apply conditional classes to task title: `{% if task.status == 'completed' %}line-through text-gray-500{% else %}text-gray-900{% endif %}`
    - Keep priority badge and tags at full opacity (no dimming)
    - Add completion timestamp display in metadata section
    - Use `{% if task.completed_at %}Completed {{ task.completed_at|timesince }} ago{% endif %}`
    - Show filled checkbox icon for completed tasks
  - [x] 4.4 Create status filter buttons in sidebar (`templates/includes/task_sidebar.html`)
    - Position below "All Tasks" link with divider above
    - Three buttons: "Active", "Completed", "All"
    - Active state styling: `{% if active_status_filter == 'active' %}bg-blue-600 text-white{% else %}text-gray-700 hover:bg-gray-50{% endif %}`
    - Use same padding and spacing as other sidebar links (px-3 py-2)
    - Add filter icon (funnel SVG) next to label
    - Add count badge for each filter option on right side
    - Link to `?status=active|completed|all` query parameters
  - [x] 4.5 Add "Mark All Complete" button to task list header (`templates/tasks/tasklist_detail.html`)
    - Position in header area next to task list title
    - Green color scheme: `bg-green-600 hover:bg-green-700 text-white`
    - Include checkmark icon before label text
    - Add HTMX attributes: `hx-post="{% url 'tasks:mark-all-complete' pk=task_list.id %}"`
    - Add confirmation: `hx-confirm="Mark all active tasks in this list as complete?"`
    - Show only when active tasks exist: `{% if active_task_count > 0 %}`
    - Responsive: full-width button on mobile, inline on desktop
  - [x] 4.6 Create archive navigation link in sidebar
    - Position below "No Due Date" link with divider above
    - Use archive box icon (SVG) from Heroicons
    - Same styling as other sidebar links
    - Link to `{% url 'tasks:archived-tasks' %}`
    - Include count badge showing number of archived tasks if any exist
    - Highlight active state when viewing archived tasks
  - [x] 4.7 Add archive buttons to task cards and headers
    - "Archive" button on individual completed tasks (small, secondary styling)
    - "Archive All Completed" button in task list header (secondary button styling)
    - Use archive icon from Heroicons
    - Add HTMX attributes: `hx-post="{% url 'tasks:archive-task' pk=task.id %}"`
    - Add confirmation for bulk archive: `hx-confirm="Archive all completed tasks?"`
    - Show only for completed tasks or when completed tasks exist
  - [x] 4.8 Update sidebar counts to "X of Y complete" format
    - Update "All Tasks" link count
    - Update "Today" link count
    - Update "Upcoming" link count
    - Update "Overdue" link count
    - Format: "{{ completed_count }} of {{ total_count }}"
    - Exclude archived tasks from all counts
    - Use efficient single-query aggregation from view context
  - [x] 4.9 Create archived tasks template (`templates/tasks/archived_task_list.html`)
    - Show archived tasks with "Unarchive" button on each
    - Use same task card template with archive-specific styling
    - Display completion timestamp
    - Empty state message: "No archived tasks" when list is empty
    - Sort by `completed_at` descending
  - [x] 4.10 Ensure UI rendering tests pass
    - Run ONLY the 2-4 tests written in 4.1
    - Verify interactive checkbox works
    - Verify status filter buttons display correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-4 tests written in 4.1 pass
- Interactive checkbox toggles task status via HTMX
- Completed tasks display with strikethrough and gray text
- Status filter buttons show active state styling
- "Mark All Complete" button appears with confirmation dialog
- Archive links and buttons display correctly
- Sidebar counts show "X of Y complete" format
- Archived tasks view displays with unarchive functionality

---

### Keyboard Shortcuts & Testing

#### Task Group 5: Alpine.js Shortcuts & Integration Testing
**Dependencies:** Task Groups 1-4

- [x] 5.0 Complete keyboard shortcuts and integration testing
  - [x] 5.1 Review tests from Task Groups 1-4
    - Review the 5 tests written for database layer (Task 1.1)
    - Review the 4 tests written for backend views (Task 2.1)
    - Review the 4 tests written for bulk actions (Task 3.1)
    - Review the 4 tests written for UI rendering (Task 4.1)
    - Total existing tests: 17 tests
  - [x] 5.2 Add Alpine.js keyboard shortcuts to task list container
    - Add `x-data="{ focusedTaskId: null }"` to task list container
    - Add `@keydown.window.x.prevent="toggleTaskCompletion($event)"` listener
    - Add `@keydown.window.c.prevent="toggleTaskCompletion($event)"` listener
    - Implement `toggleTaskCompletion` function to find focused/hovered task
    - Trigger checkbox click programmatically
    - Prevent default keyboard action to avoid browser conflicts
    - Add visual feedback animation on keyboard activation (brief highlight)
  - [x] 5.3 Add task focus tracking for keyboard shortcuts
    - Add `@mouseenter="focusedTaskId = {{ task.id }}"` to each task card
    - Add `@mouseleave="focusedTaskId = null"` to each task card
    - Use `focusedTaskId` to determine which task to toggle
    - Fallback to first task if no task is focused
  - [x] 5.4 Write 6 integration tests for end-to-end workflows
    - End-to-end task completion toggle workflow (mark complete → positioned at bottom → timestamp set)
    - End-to-end status filtering workflow (change filter → preference persists → correct tasks shown)
    - Bulk complete workflow (mark all → verify all completed → counts updated)
    - Archive workflow (archive task → removed from view → shown in archive)
    - Unarchive workflow (unarchive → restored to normal view)
    - Bulk archive workflow (archive all completed → verify archived → counts updated)
  - [x] 5.5 Run feature-specific tests only
    - Run ONLY tests related to this spec's feature
    - Total tests: 23 tests (5 database + 4 views + 4 bulk + 4 UI + 6 integration)
    - Verify all critical workflows pass
  - [x] 5.6 Add TaskUnarchiveView for unarchive functionality
    - Create view to handle unarchiving tasks
    - Add URL pattern for unarchive endpoint
    - Update archived task template with unarchive button
  - [x] 5.7 Update tasks.md with completion status
    - Mark all sub-tasks as complete with [x]
    - Mark all parent tasks (5.0, 4.0, 3.0, 2.0, 1.0) as complete
    - Verify all checkboxes marked in tasks.md

**Acceptance Criteria:**
- All 23 feature-specific tests pass ✅
- Keyboard shortcuts ('x' and 'c') toggle task completion via Alpine.js ✅
- Alpine.js tracks focused task for keyboard actions ✅
- Visual feedback shows when keyboard shortcut activates ✅
- 6 integration tests added covering end-to-end workflows ✅
- TaskUnarchiveView implemented with URL routing ✅
- Critical user workflows for task status & completion are covered ✅
- Testing focused exclusively on this spec's feature requirements ✅

---

## Execution Order

Recommended implementation sequence:
1. **Database Layer** (Task Group 1) - Schema, migrations, model methods ✅
2. **Backend Views Layer** (Task Group 2) - Status toggle, filtering logic ✅
3. **Bulk Actions & Archive Layer** (Task Group 3) - Bulk operations, archive functionality ✅
4. **Frontend Templates & UI Layer** (Task Group 4) - Interactive components, HTMX ✅
5. **Keyboard Shortcuts & Testing** (Task Group 5) - Alpine.js, integration tests ✅

---

## Testing Philosophy

This feature follows a **focused testing approach**:
- Each task group (1-4) writes 2-5 focused tests covering ONLY critical behaviors
- Task group 5 adds 6 integration tests to cover end-to-end workflows
- **Total tests: 23 tests**
- Focus on critical user workflows, NOT comprehensive coverage
- Edge cases, performance, and accessibility testing are deferred

---

## Query Optimization Strategy

**CRITICAL: Prevent N+1 queries throughout implementation**

All task querysets must use:
- `select_related('task_list__workspace', 'created_by')` for foreign key relationships
- `prefetch_related('tags')` for many-to-many relationships
- `annotate()` with `Case/When` for sort_order instead of Python-side sorting
- `aggregate()` with `Count()` and `Q()` filters for sidebar counts in single query
- `update()` for bulk operations instead of iterating and saving individual instances
- Database indexes on `completed_at` and `is_archived` fields (added in migration)

**Example optimized query:**
```python
tasks = Task.objects.filter(
    task_list__workspace__owner=request.user,
    is_archived=False
).select_related(
    'task_list__workspace',
    'created_by'
).prefetch_related(
    'tags'
).annotate(
    sort_order=Case(
        When(status='completed', then=Value(1)),
        default=Value(0),
        output_field=IntegerField()
    )
).order_by('sort_order', '-created_at')
```

---

## Standards Compliance

**Backend Standards:**
- Follow `agent-os/standards/backend/models.md` for database schema design
- Follow `agent-os/standards/backend/queries.md` for N+1 prevention
- Use database constraints for data integrity
- Include `created_at` and `updated_at` timestamps (already exist)
- Index foreign keys and frequently queried columns

**Frontend Standards:**
- Follow `agent-os/standards/frontend/components.md` for HTMX patterns
- Use Alpine.js for client-side state management
- Apply Tailwind utility classes for all styling
- Keep JavaScript minimal and focused

**Testing Standards:**
- Follow `agent-os/standards/testing/test-writing.md` for test philosophy
- Test critical paths and primary workflows only
- Mock external dependencies
- Keep tests fast (milliseconds)

---

## Code Reuse Patterns

**Model Methods:**
- Reuse existing `mark_complete()` and `mark_active()` methods (lines 455-460)
- Extend with `completed_at` timestamp management
- Follow existing `TaskManager.active()` and `completed()` methods (lines 258-262)

**View Filtering:**
- Replicate workspace and tag filtering logic from `TaskListView.get_queryset()` (lines 339-384)
- Follow query parameter pattern using `request.GET.get()`
- Reuse `select_related()` and `prefetch_related()` optimization patterns

**HTMX Patterns:**
- Follow existing hx-get pattern from Edit button in task card
- Use `hx-target` and `hx-swap` for partial updates
- Include `HX-Trigger` response header for list refresh

**Sidebar Navigation:**
- Follow existing sidebar link structure for consistency
- Use same active state styling pattern as due date views
- Follow count badge pattern from existing sidebar links

---

## Visual Design Notes

**Status Filter Buttons:**
- Active state: `bg-blue-600 text-white`
- Inactive state: `text-gray-700 hover:bg-gray-50`
- Include filter icon (funnel SVG) next to label
- Show count badge for each option

**Completed Task Visual:**
- Title: `line-through text-gray-500`
- Checkbox: filled/checked state with blue accent
- Priority badge and tags: full opacity (no dimming)
- Completion timestamp in metadata section

**Bulk Action Buttons:**
- "Mark All Complete": `bg-green-600 hover:bg-green-700 text-white`
- "Archive All Completed": secondary button styling
- Include confirmation dialogs for destructive actions

**Archive Link:**
- Archive box icon from Heroicons
- Same styling as other sidebar links
- Count badge if archived tasks exist

---

## Out of Scope

The following features are explicitly OUT OF SCOPE for T008:
- Bulk status changes via multi-select checkboxes (deferred to T013: Bulk Task Actions)
- Partial completion or progress tracking (0-100% done indicators)
- Additional status values beyond active/completed (no "in progress", "blocked", etc.)
- Recurring task handling on completion (separate recurring tasks feature)
- Editable completion timestamps (always system-managed)
- Permanent task deletion (use archive only)
- Restore deleted/archived tasks in bulk (one at a time only)
- Status change history or audit log (separate audit feature)
- Email notifications on task completion (separate notification feature)
- Completion statistics or reports (separate analytics feature)
