# Next Features - Task Due Date Management (T010)

**Created:** January 14, 2026
**Branch:** feature-task-due-date-management
**Previous Commit:** 8a9a7cc - Implement Task Labels & Tags (T007)

## Summary of Completed Work

### ✅ Features Completed: T001-T007

**Phase 1: Authentication & Workspace** (Complete)
- User authentication and workspace management
- Permission system and user profiles

**Phase 2: Core Task CRUD (T001-T006)** (Complete - 32/32 tests)
- Basic task CRUD operations
- Task title, description, due date, due time, priority levels
- TaskList hierarchy and organization

**Phase 3: Task Labels & Tags (T007)** (Complete - 39/39 tests)
- Tag model with workspace scoping
- Comma-separated tag input and automatic creation
- Tag filtering and color-coded badges
- Query optimization

**Total Tests Passing:** 71+ tests across all features

## Next Feature: T010 - Task Due Date Management

**Priority:** P0 (High Priority for MVP)
**Description:** Enhanced due date views and management
**Branch:** feature-task-due-date-management
**Estimated Time:** 4-6 hours
**Complexity:** Low-Medium

### Why This Feature Next?

1. **Builds on existing foundation:** We already have due_date and due_time fields
2. **High user value:** "Today", "Upcoming", and "Overdue" views are essential
3. **Low complexity:** Primarily view logic and filtering (no new models)
4. **Quick win:** Can be completed in one session
5. **Core workflow:** Time management is fundamental to task management

### Feature Requirements

According to user needs and task management best practices:

#### Core Views
1. **Today View** - Tasks due today
2. **Upcoming View** - Tasks due in next 7 days
3. **Overdue View** - Tasks past due date (active only)
4. **No Due Date View** - Tasks without due dates

#### Quick Actions
- Set due date to "Today"
- Set due date to "Tomorrow"
- Set due date to "Next Week" (7 days from now)
- Set due date to "Custom" (date picker)

#### Visual Indicators
- Red badge for overdue tasks
- Yellow badge for today's tasks
- Orange badge for upcoming (within 3 days)
- Gray for no due date

#### Filtering & Sorting
- Sort by due date (earliest first)
- Filter by date range
- Combine with tag filtering

### Implementation Plan

#### 1. Views Layer (Primary Focus)
- **Create DueDateViewMixin** for common date filtering logic
- **TasksTodayView** - Filter tasks due today
- **TasksUpcomingView** - Filter tasks due in next 7 days
- **TasksOverdueView** - Filter overdue tasks
- **TasksNoDueDateView** - Filter tasks without due dates
- Update TaskListView to support date_filter query parameter

#### 2. Forms Layer (Minor Updates)
- Add due date quick action buttons to TaskForm
- JavaScript/Alpine.js to set date on button click
- Visual date picker enhancements

#### 3. Templates Layer
- **Navigation links** for Today/Upcoming/Overdue
- **Date badges** with color coding on task cards
- **Quick action buttons** in task form
- **Date range selector** in task list header
- Update task card template to show enhanced date badges

#### 4. URL Routing
```python
path('tasks/today/', TasksTodayView.as_view(), name='tasks-today')
path('tasks/upcoming/', TasksUpcomingView.as_view(), name='tasks-upcoming')
path('tasks/overdue/', TasksOverdueView.as_view(), name='tasks-overdue')
path('tasks/no-due-date/', TasksNoDueDateView.as_view(), name='tasks-no-due-date')
```

#### 5. Testing
- Test today view filtering (2 tests)
- Test upcoming view date range (2 tests)
- Test overdue view filtering (2 tests)
- Test no due date filtering (2 tests)
- Test date badge display (2 tests)
- **Target:** 10-12 tests

### Task Breakdown

**Task Group 1: Views & Filtering** (6 tests)
- Create DueDateViewMixin
- Implement TasksTodayView
- Implement TasksUpcomingView
- Implement TasksOverdueView
- Implement TasksNoDueDateView
- Write view tests

**Task Group 2: Templates & Navigation** (4 tests)
- Add navigation links (Today/Upcoming/Overdue)
- Update task card date badges
- Add date quick actions to form
- Add date range selector
- Write template rendering tests

**Task Group 3: Forms Enhancement** (Optional)
- Add quick action buttons to TaskForm
- Alpine.js for date setting
- Visual enhancements

**Task Group 4: URL Routing**
- Add new URL patterns
- Update URL tests

### Success Criteria

- ✅ Users can view tasks due today
- ✅ Users can view upcoming tasks (next 7 days)
- ✅ Users can view overdue tasks
- ✅ Tasks display with color-coded date badges
- ✅ Navigation includes Today/Upcoming/Overdue links
- ✅ Date views can be combined with tag filtering
- ✅ 10-12 tests pass
- ✅ Responsive design on all devices

### Files to Create/Modify

**New Files:**
- `agent-os/specs/2026-01-14-task-due-date-management/tasks.md`
- `agent-os/specs/2026-01-14-task-due-date-management/spec.md`
- `tasks/tests/test_task_due_date_views.py`

**Modified Files:**
- `tasks/views.py` (add new views)
- `tasks/urls.py` (add new URL patterns)
- `templates/includes/nav.html` (add date view links)
- `templates/tasks/task_list.html` (enhanced date badges)
- `templates/tasks/_task_form_fields.html` (optional quick actions)

### Dependencies

- None! This feature builds entirely on existing infrastructure

### Alternative Next Features

If T010 doesn't seem like the right fit, alternatives include:

**T008: Task Status & Completion**
- Enhanced status management
- Completion tracking
- Archive functionality

**T009: Task Search**
- Full-text search
- Search across workspaces
- Search results page

**T011: Task Ordering & Moving**
- Drag-drop reordering
- Move between task lists
- Position tracking

## Recommendation

**Proceed with T010 (Task Due Date Management)** because:
1. Lowest complexity of the high-priority features
2. Builds directly on existing due_date field
3. High user value for time management
4. Can be completed quickly (4-6 hours)
5. Sets up foundation for calendar views later

After T010, implement T008 (Status) → T009 (Search) → T011 (Ordering) for a complete MVP.

---

**Ready to start?** Create the feature branch:
```bash
git checkout -b feature-task-due-date-management
```
