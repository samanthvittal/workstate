# Specification: Task Status & Completion

## Goal
Enable users to complete tasks with interactive checkboxes, filter tasks by status (Active/Completed/All), and archive completed tasks, with automatic positioning of completed tasks at the bottom of lists and persistent user preferences for filter state.

## User Stories
- As a user, I want to click a checkbox on a task card to mark it complete so I can quickly update task status without leaving the list view
- As a user, I want to use keyboard shortcuts (x or c) to toggle completion so I can update tasks efficiently without using the mouse
- As a user, I want to filter tasks by status (Active/Completed/All) in the sidebar so I can focus on relevant tasks
- As a user, I want my status filter preference to persist across sessions so I don't have to reselect my preferred view each time
- As a user, I want completed tasks to automatically move to the bottom of the list so active tasks remain at the top for easy access
- As a user, I want to see when tasks were completed so I can track completion history
- As a user, I want a "Mark All Complete" button with confirmation so I can quickly complete all tasks in a list
- As a user, I want to archive completed tasks so I can hide them from normal views while keeping them in the database
- As a user, I want sidebar counts to show "X of Y complete" format so I understand completion progress at a glance
- As a user, I want visual strikethrough on completed tasks so I can distinguish them from active tasks

## Specific Requirements

**Database Schema Changes**
- Add `completed_at` field to Task model (DateTimeField, nullable, indexed, db_index=True)
- Add `is_archived` field to Task model (BooleanField, default=False, indexed, db_index=True)
- Add `default_task_status_filter` field to UserPreference model (CharField, max_length=20, choices=['active', 'completed', 'all'], default='active')
- Create database migration to add new fields without data loss
- Backfill `completed_at` for existing completed tasks using `updated_at` value
- Add composite index on (task_list, status, is_archived) for efficient filtering
- Add database constraint to ensure completed_at is only set when status='completed'

**Interactive Completion Toggle**
- Replace disabled checkbox in task card template with interactive HTMX-powered checkbox
- Add hx-post attribute to checkbox pointing to new toggle-status endpoint
- Use hx-target="#task-{{ task.id }}" and hx-swap="outerHTML" for in-place task card replacement
- Create TaskToggleStatusView handling POST requests to flip task status
- Update completed_at timestamp when marking task complete (set to timezone.now())
- Clear completed_at timestamp when marking task active again
- Return updated task card partial HTML after status change
- Preserve task position in list based on current filter and ordering rules

**Status Filtering with User Preference**
- Add status filter buttons to task sidebar (Active/Completed/All)
- Position filter buttons near top of sidebar above "Due Date Views" section
- Apply active state styling (bg-blue-600 text-white) to current filter
- Store selected filter in UserPreference.default_task_status_filter field
- Load user's default filter on initial page load if no query parameter present
- Update filter via query parameter (?status=active|completed|all) for sharing links
- Modify TaskListView.get_queryset() to apply status filter
- Exclude archived tasks from all views (is_archived=False filter always applied)

**Completed Task Positioning**
- Annotate tasks with sort_order using Case/When expressions (completed=1, active=0)
- Order tasks by sort_order first, then by created_at descending
- Apply ordering in all task list views (task_list.html, tasklist_detail.html, dashboard)
- Ensure completed tasks always appear after active tasks regardless of creation date
- Maintain secondary ordering within each status group by created_at descending
- Update TaskManager methods to include proper ordering

**Completion Timestamp Display**
- Display "Completed X ago" on hover over completed task cards using title attribute
- Use Django's timesince template filter for relative time display
- Show absolute timestamp in task detail view ("Completed on Jan 15, 2026 at 3:45 PM")
- Include completed_at in task card metadata section for completed tasks
- Use user's timezone preference from UserPreference model for display

**Mark All Complete Bulk Action**
- Add "Mark All Complete" button to tasklist detail view header
- Show button only when viewing specific task list (not in all tasks view)
- Use hx-post to bulk complete endpoint with hx-confirm for confirmation dialog
- Confirmation message: "Mark all active tasks in this list as complete?"
- Create TaskListMarkAllCompleteView handling bulk status updates
- Update only active (non-completed) tasks in transaction for data consistency
- Set completed_at timestamp for all newly completed tasks
- Return success message with count via Django messages framework
- Refresh task list after bulk action using HX-Trigger header

**Archive Functionality**
- Add "Archive" link to task sidebar navigation below "No Due Date" link
- Create TaskArchiveView to handle archiving single tasks via POST request
- Set is_archived=True on task, keeping all other data intact (soft delete)
- Create ArchivedTaskListView showing only archived tasks (is_archived=True filter)
- Include "Unarchive" button on archived tasks to restore (set is_archived=False)
- Create TaskListArchiveAllCompletedView for bulk archiving completed tasks
- Add "Archive All Completed" button to tasklist detail view with confirmation
- Exclude archived tasks from all counts (active_count, completed_count, sidebar badges)
- Sort archived tasks by completed_at descending (most recently completed first)

**Sidebar Counts Update**
- Change count format from single number to "X of Y complete" format
- X = completed task count (status='completed', is_archived=False)
- Y = total task count (status in ['active', 'completed'], is_archived=False)
- Update counts in "All Tasks" link, "Today" link, "Upcoming" link, "Overdue" link
- Use annotate() with Count() and filter Q objects for efficient single-query counts
- Cache counts using Django's cache framework (5 minute TTL) for performance
- Invalidate cache on task status change, creation, or archive actions

**Query Optimization Strategy**
- Use select_related('task_list__workspace', 'created_by') on all task querysets
- Use prefetch_related('tags') for tasks with tag relationships
- Use annotate() with Case/When for sort_order instead of Python-side sorting
- Use aggregate() with Count() and Q() filters for sidebar counts in single query
- Add database indexes on completed_at and is_archived fields
- Use update() for bulk operations instead of iterating and saving individual instances
- Use only() and defer() to limit columns fetched when full objects not needed

**Keyboard Shortcuts with Alpine.js**
- Add Alpine.js x-data directive to task list container
- Add @keydown.window.x="toggleTaskCompletion($event)" listener
- Add @keydown.window.c="toggleTaskCompletion($event)" listener
- Implement toggleTaskCompletion function to find focused/hovered task and trigger checkbox
- Prevent default keyboard action to avoid conflicts with browser shortcuts
- Show visual feedback when keyboard shortcut activates (brief highlight animation)

**Visual States for Completed Tasks**
- Add line-through text decoration to task title when status='completed'
- Change text color to text-gray-500 for completed task titles
- Keep checkbox checked state for completed tasks
- Show filled checkbox icon instead of empty checkbox for completed tasks
- Maintain all other styling (priority badge, tags, metadata) without changes
- Use Tailwind utility classes for all styling (no custom CSS required)

## Visual Design

**Status Filter Buttons (Sidebar)**
- Position immediately below "All Tasks" link with divider above
- Three buttons in vertical stack: Active, Completed, All
- Active button: bg-blue-600 text-white when selected, text-gray-700 hover:bg-gray-50 when not selected
- Use same padding and spacing as other sidebar links (px-3 py-2)
- Include small filter icon (funnel SVG) next to label
- Show count badge for each filter option on right side

**Archive Link (Sidebar)**
- Position below "No Due Date" link with divider above
- Use archive box icon (SVG) from Heroicons
- Same styling as other sidebar links
- Include count badge showing number of archived tasks if any exist
- Highlight active state when viewing archived tasks

**Mark All Complete Button**
- Position in header area next to task list title
- Use green color scheme (bg-green-600 hover:bg-green-700)
- Include checkmark icon before label text
- Show only on tasklist detail view when active tasks exist
- Responsive: full-width button on mobile, inline on desktop

**Archive Buttons**
- "Archive" button on individual completed tasks (small, secondary styling)
- "Archive All Completed" button in header (secondary button styling)
- Use archive icon from Heroicons
- Show only for completed tasks or when completed tasks exist

**Completed Task Visual**
- Title text with line-through decoration and text-gray-500 color
- Filled checkbox (checked state) with blue accent color
- Keep priority badge and tags at full opacity (no dimming)
- Show "Completed X ago" text in metadata section
- Position at bottom of list after all active tasks

## Existing Code to Leverage

**Task Model Methods (tasks/models.py)**
- Use existing mark_complete() method (line 455) to set status='completed'
- Use existing mark_active() method (line 460) to set status='active'
- Extend methods to also update completed_at timestamp
- Use existing TaskManager.active() (line 258) and completed() (line 262) methods
- Use existing indexes on status field for efficient filtering
- Follow existing CheckConstraint pattern for status validation (line 441)

**TaskListView Filtering Pattern (tasks/views.py)**
- Replicate workspace and tag filtering logic from get_queryset() (lines 339-384)
- Follow query parameter pattern using request.GET.get() for status filter
- Reuse prefetch_related('tags') and select_related() optimization patterns (line 343)
- Apply same user access control via task_list__workspace__owner filter
- Use existing get_due_date_counts() method pattern for status counts

**HTMX Task Card Pattern (templates/tasks/_task_card.html)**
- Replace disabled checkbox (line 12) with interactive HTMX checkbox
- Follow existing hx-get pattern from Edit button (line 79) but use hx-post
- Use hx-target="#task-{{ task.id }}" and hx-swap="outerHTML" for replacement
- Include HX-Trigger response header pattern from TaskQuickDateView (line 325)
- Maintain existing task card structure and styling

**Sidebar Navigation Pattern (templates/includes/task_sidebar.html)**
- Add status filter buttons following existing link structure (lines 6-17)
- Use same active state styling pattern as due date views (line 31)
- Follow count badge pattern from existing sidebar links (lines 14-16)
- Maintain consistent spacing and dividers between sections

**UserPreference Model (accounts/models.py)**
- Add default_task_status_filter field following existing CharField pattern (lines 160-177)
- Use same choices tuple pattern as DATE_FORMAT_CHOICES (line 131)
- Access via request.user.preferences.default_task_status_filter
- Update in view when user changes filter selection

## Out of Scope
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
