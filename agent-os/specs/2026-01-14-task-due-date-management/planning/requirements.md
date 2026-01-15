# Requirements - Task Due Date Management (T010)

**Feature:** Enhanced due date views and management
**Spec Folder:** agent-os/specs/2026-01-14-task-due-date-management
**Date:** January 14, 2026

## User Requirements (Gathered from Q&A)

### 1. Today View
- **Scope:** Show ONLY tasks with `due_date = today`
- **Strict filtering:** Do NOT include overdue tasks
- **Navigation:** Accessible from main sidebar + global filter bar

### 2. Upcoming View
- **Default:** Tasks due in next 7 days (from tomorrow onwards)
- **Optional Filters:** 14 days, 30 days view options
- **Exclude:** Today's tasks (separate view)
- **Navigation:** Accessible from main sidebar + global filter bar

### 3. Overdue View
- **Filter Logic:** `due_date < today` AND `status != completed`
- **Sorting:** Oldest first (most overdue at top)
- **Navigation:** Accessible from main sidebar + global filter bar

### 4. No Due Date View
- **Filter Logic:** Tasks where `due_date IS NULL`
- **Purpose:** Find tasks without deadlines

### 5. Quick Date Actions
Buttons for setting due dates quickly:
- **"Today"** - Set due_date to current date
- **"Tomorrow"** - Set due_date to tomorrow
- **"Next Week"** - Set due_date to next Monday
- **"Clear Due Date"** - Remove due_date (set to NULL)

**Availability:**
- Task detail/edit modal
- Inline in list view (on hover or click)
- Bulk operations for multi-selected tasks

### 6. Visual Indicators
Color-coded labels for due date status:
- **Red** - Overdue tasks (due_date < today, not completed)
- **Yellow/Amber** - Tasks due today
- **Green/Neutral** - Upcoming tasks (due in future)
- **Gray** - Tasks with no due date

**Implementation:** Color-coded labels (not background colors or icons alone)

### 7. Navigation Integration
- **Primary:** Main navigation sidebar links
  - "Today" view link
  - "Upcoming" view link
  - "Overdue" view link
- **Secondary (if possible):** Quick filters in global filter bar

### 8. Features OUT OF SCOPE
The following are part of "Task Scheduling" (separate feature in spec.md):
- ❌ Recurring task due date logic
- ❌ Time-of-day due times (e.g., 3pm vs end-of-day)
- ❌ Calendar view integration
- ❌ Notification/reminder triggers

### 9. Code Reuse Strategy
- Use existing UI components and patterns
- Follow current navigation layout patterns
- Re-use existing task filtering logic from TaskListView
- Leverage existing Task model (due_date, due_time fields already exist)

### 10. Visual Assets
- None provided
- Reference existing UI patterns in codebase

## Technical Context

### Existing Infrastructure
- **Task Model:** Has `due_date` and `due_time` fields
- **TaskListView:** Supports filtering (see tag filtering implementation)
- **Navigation:** Sidebar navigation exists
- **Forms:** TaskForm handles task editing
- **Templates:** Task cards, task lists already display due dates

### Files to Reference
- `tasks/models.py` - Task model with due_date field
- `tasks/views.py` - TaskListView filtering patterns
- `tasks/forms.py` - TaskForm for quick actions
- `templates/includes/nav.html` - Sidebar navigation
- `templates/tasks/task_list.html` - Task card templates
- `templates/tasks/_task_form_fields.html` - Form field templates

## Success Criteria

- ✅ Users can view tasks due today (strict - only today)
- ✅ Users can view upcoming tasks (7/14/30 day filters)
- ✅ Users can view overdue tasks (sorted oldest first)
- ✅ Users can view tasks without due dates
- ✅ Tasks display with color-coded date labels
- ✅ Navigation includes Today/Upcoming/Overdue links in sidebar
- ✅ Quick date actions available in modal, inline, and bulk operations
- ✅ Date views can be combined with tag filtering
- ✅ 10-12 tests pass
- ✅ Responsive design on all devices

## Implementation Priority

**P0 (High Priority for MVP)**
- Estimated Time: 4-6 hours
- Complexity: Low-Medium
- Dependencies: None (builds on existing due_date field)
