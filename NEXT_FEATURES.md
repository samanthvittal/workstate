# Next Features - Task Labels & Tags (T007)

**Created:** January 14, 2026
**Branch:** feature-task-labels-tags
**Previous Commit:** 75c8e90 - Implement Core Task CRUD & TaskList Organization (T001-T006)

## Summary of Completed Work

### ✅ Tasks Completed: T001-T006

We have successfully implemented the foundation of Workstate's task management system:

**T001 - Basic Task CRUD**
- Create, read, update, delete tasks
- TaskList organization for better categorization
- Full CRUD operations with permission checking

**T002 - Task Title**
- Required field with validation
- 255 character limit
- Whitespace trimming

**T003 - Task Description**
- Markdown support
- Optional field
- 10,000 character limit

**T004 - Due Date**
- Date picker with proper validation
- Overdue detection

**T005 - Due Time**
- Optional time field
- Validation: requires due_date if set

**T006 - Priority Levels**
- 4 levels: P1 (Urgent), P2 (High), P3 (Medium), P4 (Low)
- Color-coded badges (Red, Orange, Yellow, Blue)
- Visual indicators throughout UI

### ✅ Additional Enhancements Completed

**TaskList Feature (Beyond Core Spec)**
- Workspace → TaskLists → Tasks hierarchy
- TaskList CRUD operations
- Data migration from old structure
- 4 migrations with safe data handling

**Navigation & UX Improvements**
- Modern navigation bar with dropdowns
- Workspace selector (always visible)
- User menu with avatar/initials
- Dashboard redesign with task lists
- Fixed alignment issues

**Test Coverage**
- 32/32 tests passing (100%)
- Comprehensive test coverage across forms, views, templates, and integration

## Next Feature: T007 - Labels/Tags

**Priority:** P0 (Critical for MVP)
**Description:** Multiple tags per task for categorization
**Branch:** feature-task-labels-tags

### Feature Requirements

According to the spec (workstate/spec.md line 176):
- Multiple tags per task
- Tag creation and management
- Tag filtering and search
- Color-coded tags (optional)
- Tag autocomplete/suggestions

### Implementation Plan

#### 1. Database Layer
- **Tag Model**
  - `name` (CharField, max 50, required, unique per workspace)
  - `color` (CharField, optional, hex color)
  - `workspace` (ForeignKey to Workspace)
  - `created_by` (ForeignKey to User)
  - `created_at`, `updated_at` (auto timestamps)

- **Task-Tag Relationship**
  - Many-to-Many relationship via `tags` field on Task model
  - Or through model for additional metadata (order, etc.)

#### 2. Forms Layer
- Update TaskForm to include tags field
- Tag selection widget (multi-select or tag input)
- Tag creation inline (if tag doesn't exist, create it)
- TagForm for managing tags separately

#### 3. Views Layer
- Tag CRUD views (optional: may use inline creation only)
- Update TaskCreateView and TaskUpdateView for tags
- Tag filtering in task list views
- Tag management page (optional for MVP)

#### 4. Templates Layer
- Tag input field in task forms
- Tag display on task cards/lists
- Tag badges with colors
- Tag filtering UI
- Tag autocomplete (Alpine.js)

#### 5. URL Routing
- Tag management URLs (if separate views)
- Tag filtering URLs (`/tasks/?tag=work`)

### Estimated Complexity

**Database:** Low - Simple many-to-many relationship
**Backend:** Medium - Tag creation logic, filtering
**Frontend:** Medium - Tag input UI, autocomplete
**Tests:** Medium - Tag CRUD, filtering, validation

### Success Criteria

- ✅ Users can add multiple tags to tasks
- ✅ Tags can be created inline while creating/editing tasks
- ✅ Tags display on task cards with colors
- ✅ Users can filter tasks by tags
- ✅ Tag names are unique per workspace
- ✅ Tests cover tag creation, validation, filtering
- ✅ Responsive design on all devices

## Alternative: T032-T033 First

If labels/tags seem too complex, we could instead implement:

**T032 - Task Ordering** (P0)
- Manual drag-drop reordering within task list
- Position field on Task model
- jQuery UI Sortable or SortableJS
- HTMX for position updates

**T033 - Task Moving** (P0)
- Move tasks between task lists
- Move tasks between workspaces (with permission check)
- Dropdown or drag-drop interface

Both are P0 priority and might be simpler to implement as they build on existing TaskList functionality.

## Recommendation

**Proceed with T007 (Labels/Tags)** because:
1. It's P0 priority (critical for MVP)
2. It's a natural extension of task creation
3. Users expect tagging in modern task managers
4. It enables better task organization and filtering
5. Foundation for future features (smart lists, filters)

Let me know which feature you'd like to implement next!
