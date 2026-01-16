# Task Breakdown: Time Tracking (TT001-TT014)

## Overview
Total Task Groups: 11
Estimated Total Tasks: 90+

This comprehensive time tracking implementation includes core timer functionality, manual time entry, advanced features (idle detection, Pomodoro, time rounding, billable rates), and reporting/analytics.

## Task List

### Task Group 1: Database Models and Migrations
**Dependencies:** None

- [x] 1.0 Complete database layer for time tracking
  - [x] 1.1 Write 2-8 focused tests for TimeEntry and TimeGoal models
    - Limit to 2-8 highly focused tests maximum
    - Test only critical model behaviors (timer state transitions, duration calculation, single active timer constraint, task association requirement)
    - Skip exhaustive coverage of all methods and edge cases
  - [x] 1.2 Create TimeEntry model with validations
    - Fields: user (FK to User), task (FK to Task), project (FK to Project, nullable, inherited from task), start_time (DateTimeField, nullable), end_time (DateTimeField, nullable), duration (DurationField, required), description (TextField, blank), is_running (BooleanField, default False), is_billable (BooleanField, default False), billable_rate (DecimalField, nullable), currency (CharField, default 'USD'), created_at, updated_at
    - Validations: end_time must be after start_time if both present, duration must be positive, only one running timer per user, task is required
    - Database constraints: CHECK constraint for end_time > start_time, UNIQUE partial index on (user_id, is_running=True) for single active timer enforcement
    - Indexes: user_id, task_id, project_id, start_time, is_running, is_billable
    - Methods: calculate_duration(), stop(), get_elapsed_time(), apply_rounding()
    - Reuse pattern from: Task model (created_at/updated_at, clean() validation)
  - [x] 1.3 Create TimeEntryTag model for many-to-many relationship
    - Fields: time_entry (FK to TimeEntry), tag (FK to Tag), created_at
    - Indexes: time_entry_id, tag_id
    - Follow pattern from: existing tag relationship models
  - [x] 1.4 Create TimeGoal model for time budgets
    - Fields: user (FK to User), project (FK to Project, nullable), task (FK to Task, nullable), goal_type (CharField, choices: daily/weekly/monthly/total), target_duration (DurationField), start_date (DateField, nullable), end_date (DateField, nullable), is_active (BooleanField, default True), created_at, updated_at
    - Validations: must have either project or task (not both), target_duration must be positive, end_date after start_date if both present
    - Indexes: user_id, project_id, task_id, goal_type, is_active
    - Methods: get_progress(), get_percentage_complete(), is_overbudget()
  - [x] 1.5 Create UserTimePreferences model for user settings
    - Fields: user (OneToOneField to User), rounding_interval (IntegerField, choices: 0/5/10/15/30, default 0), rounding_method (CharField, choices: up/down/nearest, default 'nearest'), idle_threshold_minutes (IntegerField, default 5), pomodoro_work_minutes (IntegerField, default 25), pomodoro_break_minutes (IntegerField, default 5), default_billable_rate (DecimalField, nullable), default_currency (CharField, default 'USD'), created_at, updated_at
    - Validations: all minute/interval fields must be positive
    - One-to-one relationship ensures one preferences record per user
  - [x] 1.6 Create PomodoroSession model for Pomodoro tracking
    - Fields: time_entry (FK to TimeEntry), session_number (IntegerField), started_at (DateTimeField), completed_at (DateTimeField, nullable), was_completed (BooleanField, default False), break_taken (BooleanField, default False), created_at
    - Indexes: time_entry_id, started_at
    - Methods: complete_session(), mark_break_taken()
  - [x] 1.7 Create migrations for all models
    - Separate migration for each model (reversible)
    - Add all indexes and constraints in migrations
    - Create migration for partial unique index on TimeEntry (user_id, is_running=True) using raw SQL
    - Ensure migration order: TimeEntry -> TimeEntryTag -> TimeGoal -> UserTimePreferences -> PomodoroSession
  - [x] 1.8 Set up model associations and managers
    - TimeEntry.objects.running() manager method for active timers
    - TimeEntry.objects.for_user(user) manager method with permission checks
    - Configure reverse relations: task.time_entries, project.time_entries, user.time_entries
    - Add related_name parameters for clean reverse lookups
  - [x] 1.9 Ensure database layer tests pass
    - Run ONLY the 2-8 tests written in 1.1
    - Verify migrations run successfully
    - Verify single active timer constraint works at database level
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1 pass
- All models pass validation tests
- Migrations run successfully and are reversible
- Single active timer constraint enforced at database level
- All associations work correctly

---

### Task Group 2: Redis Cache Layer for Active Timers
**Dependencies:** Task Group 1 (COMPLETED)

- [x] 2.0 Complete Redis integration for timer state
  - [x] 2.1 Write 2-8 focused tests for Redis timer operations
    - Limit to 2-8 highly focused tests maximum
    - Test only critical cache operations (set active timer, get active timer, clear timer, fallback to PostgreSQL on Redis failure)
    - Skip exhaustive testing of all cache scenarios
  - [x] 2.2 Create TimeEntryCache service class
    - Location: time_tracking/services/cache.py
    - Methods: set_active_timer(user_id, time_entry_data), get_active_timer(user_id), clear_active_timer(user_id), sync_to_db(user_id)
    - Use Redis keys pattern: "timer:active:{user_id}"
    - Store serialized timer data with TTL of 24 hours
    - Implement automatic fallback to PostgreSQL if Redis unavailable
  - [x] 2.3 Implement timer state synchronization
    - Sync Redis cache to PostgreSQL every 60 seconds via Celery task
    - Restore active timers from PostgreSQL to Redis on app startup
    - Handle race conditions between cache and database updates
  - [x] 2.4 Add cache invalidation on timer stop/discard
    - Clear Redis cache immediately when timer stopped
    - Update cache when timer description edited
    - Ensure cache consistency across operations
  - [x] 2.5 Ensure Redis cache layer tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify cache operations work correctly
    - Verify fallback to PostgreSQL works
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- Redis cache stores and retrieves active timers correctly
- Fallback to PostgreSQL works when Redis unavailable
- Cache stays synchronized with database

---

### Task Group 3: Core Timer API Endpoints
**Dependencies:** Task Groups 1-2

- [x] 3.0 Complete core timer API
  - [x] 3.1 Write 2-8 focused tests for timer API endpoints
    - Limit to 2-8 highly focused tests maximum
    - Test only critical actions (start timer, stop timer, discard timer, single active timer enforcement)
    - Skip exhaustive testing of all API scenarios
  - [x] 3.2 Create TimerViewSet for timer operations
    - Location: time_tracking/views/timer_views.py
    - Actions: start (POST /api/timers/start/), stop (POST /api/timers/stop/), get_active (GET /api/timers/active/), discard (POST /api/timers/discard/)
    - Follow pattern from: existing DRF ViewSet patterns
    - Use TimeEntryCache service for active timer state
    - Implement permission checks: user can only manage own timers
  - [x] 3.3 Implement start timer endpoint with auto-stop
    - Validate task_id provided and user has access to task
    - Check for existing active timer via Redis cache
    - If active timer exists, return confirmation dialog data (timer info, elapsed time)
    - On confirmation, stop previous timer (save to DB) and start new timer
    - Create TimeEntry with is_running=True, store in Redis and PostgreSQL
    - Support optional description field
    - Return timer data with task/project info
  - [x] 3.4 Implement stop timer endpoint
    - Validate user has active timer
    - Calculate final duration from start_time to current time
    - Apply time rounding rules from UserTimePreferences
    - Set end_time and is_running=False
    - Clear from Redis cache, save to PostgreSQL
    - Return final time entry data with rounded duration
  - [x] 3.5 Implement discard timer endpoint
    - Validate user has active timer
    - Return confirmation required response with elapsed time
    - On confirmation, delete TimeEntry record and clear from Redis
    - Do NOT create time entry record when discarding
  - [x] 3.6 Implement get active timer endpoint
    - Check Redis cache first, fallback to PostgreSQL
    - Return full timer data: id, task, project, start_time, elapsed_time, description, is_running
    - Return 404 if no active timer
    - Used by header widget for initial load
  - [x] 3.7 Add API response formatting and error handling
    - Consistent JSON responses following DRF standards
    - User-friendly error messages (never expose technical details)
    - Status codes: 200 (success), 201 (created), 400 (validation error), 403 (forbidden), 404 (not found)
    - Include elapsed_time in all timer responses (calculated, not stored)
  - [x] 3.8 Ensure timer API tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify start/stop/discard operations work
    - Verify single active timer enforcement works
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 3.1 pass
- Timer start/stop/discard endpoints work correctly
- Single active timer enforcement works across all endpoints
- Auto-stop previous timer works with confirmation dialog
- Proper authorization enforced

---

### Task Group 4: Manual Time Entry API Endpoints
**Dependencies:** Task Group 1

- [x] 4.0 Complete manual time entry API
  - [x] 4.1 Write 2-8 focused tests for time entry CRUD endpoints
    - Limit to 2-8 highly focused tests maximum
    - Test only critical actions (create entry with three modes, update entry, delete entry, validation)
    - Skip exhaustive testing of all CRUD scenarios
  - [x] 4.2 Create TimeEntryViewSet for CRUD operations
    - Location: time_tracking/views/time_entry_views.py
    - Actions: list, retrieve, create, update, partial_update, destroy
    - Follow pattern from: Task CRUD ViewSet
    - Implement permission checks: user can only access own time entries
    - Support query parameters for filtering (implemented in Task Group 7)
  - [x] 4.3 Implement create endpoint with three input modes
    - Mode A: start_time + end_time provided (calculate duration automatically)
    - Mode B: start_time + duration provided (calculate end_time automatically)
    - Mode C: duration only (leave start_time and end_time null)
    - Validate mode consistency: cannot have end_time without start_time
    - Validate end_time > start_time in Mode A
    - Validate duration is positive in all modes
    - Require task_id, optional: description, tags, is_billable, billable_rate
    - Inherit project from task automatically
    - Apply time rounding rules from UserTimePreferences
    - Return created time entry with all fields
  - [x] 4.4 Implement update and partial update endpoints
    - Allow editing all fields except user_id
    - Recalculate duration when start_time or end_time changed
    - Prevent editing is_running=True entries (must use timer API)
    - Validate same rules as create (end_time > start_time, positive duration)
    - Apply time rounding rules to updated duration
  - [x] 4.5 Implement delete endpoint
    - Soft delete or hard delete based on business requirements
    - Prevent deleting is_running=True entries (must discard via timer API)
    - Return 204 No Content on success
  - [x] 4.6 Implement list endpoint with basic serialization
    - Return time entries ordered by start_time DESC (newest first)
    - Include related data: task name, project name, tags
    - Support pagination (default 50 per page)
    - Basic filtering by date range will be enhanced in Task Group 7
  - [x] 4.7 Implement retrieve endpoint
    - Return single time entry with all related data
    - Include task details, project details, tags, user info
    - Return 404 if not found or user doesn't have access
  - [x] 4.8 Ensure time entry API tests pass
    - Run ONLY the 2-8 tests written in 4.1
    - Verify create works with all three modes
    - Verify update/delete work correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 4.1 pass
- CRUD operations work correctly
- Three input modes validated and working
- Running timers cannot be edited/deleted via this API
- Proper authorization enforced

---

### Task Group 5: Header Timer Widget UI
**Dependencies:** Task Groups 2-3

- [x] 5.0 Complete header timer widget
  - [x] 5.1 Write 2-8 focused tests for timer widget component
    - Limit to 2-8 highly focused tests maximum
    - Test only critical behaviors (widget renders active timer, live countdown updates, stop/discard buttons work)
    - Skip exhaustive testing of all widget states
  - [x] 5.2 Create timer widget template component
    - Location: templates/time_tracking/components/timer_widget.html
    - Include in: templates/base.html header (visible on all authenticated pages)
    - Display: elapsed time (live updating), task name, project name, stop button, quick edit button, discard button
    - Use Alpine.js for client-side elapsed time countdown (updates every second)
    - Collapse to icon-only mode on mobile (screens < 768px)
    - Show/hide based on active timer state
  - [x] 5.3 Implement Alpine.js timer countdown logic
    - Alpine component: x-data="timerWidget"
    - Data: startTime, elapsedSeconds, isRunning, taskName, projectName, description
    - Method: updateElapsed() - calculates elapsed time every second using setInterval
    - Format elapsed time as HH:MM:SS
    - Start countdown on component mount if timer active
    - Update UI reactively when elapsed time changes
  - [x] 5.4 Add HTMX actions for stop and discard
    - Stop button: POST to /timers/stop/ via HTMX, update widget on success
    - Discard button: DELETE to /timers/active/ via HTMX, show confirmation dialog first
    - Quick edit button: Open inline edit form for description field
    - Use hx-target to update widget container on response
    - Show loading states during API calls
  - [x] 5.5 Implement confirmation dialog for discard
    - Use Alpine.js modal component pattern
    - Display elapsed time being discarded
    - Show clear warning about data loss
    - Buttons: Cancel (close modal), Discard (proceed with DELETE request)
    - Prevent accidental clicks with modal backdrop
  - [x] 5.6 Apply responsive design and styling
    - Desktop (1024px+): Full widget with all info and buttons
    - Tablet (768px-1024px): Compact layout with abbreviated labels
    - Mobile (320px-768px): Icon-only with elapsed time, expand on tap
    - Use Tailwind CSS utility classes following existing header patterns
    - Match design system: colors, spacing, typography from existing UI
  - [x] 5.7 Add widget initialization on page load
    - Check for active timer via GET /api/timers/active/ on page load
    - If active timer exists, initialize Alpine.js component with timer data
    - If no active timer, hide widget
    - Handle loading state during initial check
  - [x] 5.8 Ensure timer widget UI tests pass
    - Run ONLY the 2-8 tests written in 5.1
    - Verify widget renders and updates correctly
    - Verify stop/discard actions work
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 5.1 pass
- Timer widget visible on all authenticated pages when timer active
- Live elapsed time countdown updates every second
- Stop/discard buttons work correctly
- Responsive design works on all screen sizes
- Confirmation dialog prevents accidental discard

---

### Task Group 6: Timer Start Buttons in Task UI
**Dependencies:** Task Group 3

- [x] 6.0 Complete timer start/stop buttons in task views
  - [x] 6.1 Write 2-8 focused tests for timer buttons in task UI
    - Limit to 2-8 highly focused tests maximum
    - Test only critical behaviors (start timer from task, stop timer updates button state, button shows correct state)
    - Skip exhaustive testing of all button interactions
  - [x] 6.2 Add timer button to task card component
    - Location: templates/tasks/components/task_card.html
    - Button states: "Start Timer" (default) or "Stop Timer" (if task's timer is active)
    - Use HTMX to POST /timers/start/ with task_id
    - Update button state on response using hx-swap-oob
    - Position button prominently on card (top-right or near task name)
    - Follow existing task card button patterns for styling
  - [x] 6.3 Add timer button to task detail page
    - Location: templates/tasks/task_detail.html
    - Similar button states as task card
    - Position near task title/header area
    - Include optional description field input when starting timer
    - Update page state on timer start/stop without full reload
  - [x] 6.4 Add timer button to task list view
    - Location: templates/tasks/task_list.html
    - Small icon button on each task row
    - Use same HTMX pattern as task card
    - Handle auto-stop confirmation dialog if needed (show modal via Alpine.js)
  - [x] 6.5 Implement auto-stop confirmation dialog in task UI
    - Alpine.js modal component for confirmation
    - Triggered when starting timer with active timer already running
    - Display: current timer info (task, elapsed time), new task name
    - Options: Cancel, Stop & Start New, Discard & Start New
    - Handle response and update UI accordingly
  - [x] 6.6 Update button states dynamically
    - When timer started/stopped, update ALL timer buttons on page via hx-swap-oob
    - Use HTMX triggers to refresh timer button states
    - Show correct button state based on task's timer status
    - Maintain button state consistency across all task views
  - [x] 6.7 Ensure timer button UI tests pass
    - Run ONLY the 2-8 tests written in 6.1
    - Verify buttons appear in all task views
    - Verify start/stop actions work correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 6.1 pass
- Timer buttons appear on task cards, detail page, and list view
- Buttons show correct state (start vs. stop) based on timer status
- Start/stop actions work correctly via HTMX
- Auto-stop confirmation dialog works properly

---

### Task Group 7: Time Entries List View and Filters
**Dependencies:** Task Group 4

- [x] 7.0 Complete time entries list view with filtering
  - [x] 7.1 Write 2-8 focused tests for list view and filters
    - Limit to 2-8 highly focused tests maximum
    - Test only critical behaviors (default week view, date range filter, project/task filters, billable filter)
    - Skip exhaustive testing of all filter combinations
  - [x] 7.2 Create time entries list page template
    - Location: templates/time_tracking/time_entry_list.html
    - Layout: filter bar at top, time entries table/list below, daily subtotals, grand total
    - Display columns: Date, Task, Project, Duration, Start Time, End Time, Description, Billable, Rate, Revenue, Actions (edit/delete)
    - Use responsive table design (card layout on mobile)
    - Follow existing list view patterns from tasks
  - [x] 7.3 Implement default time range quick filters
    - Quick filter buttons: Current Week, Last 7 Days, Last 30 Days
    - Current Week: Monday-Sunday of current calendar week
    - Last 7 Days: Today minus 6 days to today
    - Last 30 Days: Today minus 29 days to today
    - Default view on page load: Current Week
    - Highlight active filter button
    - Update URL query parameters when filter selected
  - [x] 7.4 Implement custom date range filter
    - Date picker inputs: Start Date and End Date
    - Validate end date >= start date
    - Apply filter on form submit or date selection
    - Update URL query parameters with selected dates
    - Clear other quick filters when custom range selected
  - [x] 7.5 Implement project and task filter dropdowns
    - Project dropdown: populated from user's accessible projects
    - Task dropdown: filtered by selected project (if any), otherwise all user's tasks
    - Use Alpine.js for dependent dropdown behavior (task options update when project selected)
    - Support "All Projects" and "All Tasks" options
    - Update URL query parameters on selection
  - [x] 7.6 Implement tags multi-select filter
    - Multi-select dropdown or tag chips interface
    - Populated from all tags used in user's time entries
    - Support selecting multiple tags (OR logic: entries with any selected tag)
    - Clear button to remove all tag filters
    - Update URL query parameters with selected tag IDs
  - [x] 7.7 Implement billable status filter
    - Radio buttons or dropdown: All, Billable Only, Non-billable Only
    - Default: All (no filter)
    - Update URL query parameters on selection
    - Show revenue column only when "Billable Only" or "All" selected
  - [x] 7.8 Implement backend filtering in TimeEntryViewSet
    - Add filter_queryset() method to apply all filters
    - Date range filter: filter by start_time or created_at if start_time null
    - Project filter: filter by project_id
    - Task filter: filter by task_id
    - Tags filter: filter by time_entry_tags relationship (OR logic)
    - Billable filter: filter by is_billable field
    - Combine all filters with AND logic
    - Optimize query with select_related and prefetch_related
  - [x] 7.9 Calculate and display daily subtotals
    - Group time entries by date (using start_time or created_at if null)
    - Calculate total duration per day
    - Display subtotal row after each day's entries
    - Format duration as "Xh Ym" (e.g., "2h 30m")
  - [x] 7.10 Calculate and display grand total
    - Sum all durations in current filtered view
    - Display grand total at bottom of list
    - Show billable total and revenue total if billable filter applied
    - Update totals dynamically when filters change
  - [x] 7.11 Persist filters in URL query parameters
    - Encode all active filters in URL query string
    - Support bookmarking and sharing filtered views
    - Parse query parameters on page load to restore filter state
    - Use HTMX to update URL without full page reload when filters change
  - [x] 7.12 Ensure list view and filter tests pass
    - Run ONLY the 2-8 tests written in 7.1
    - Verify default week view loads correctly
    - Verify filters work correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 7.1 pass
- Time entries list displays correctly with all columns
- Default "Current Week" view loads on page load
- All filters work correctly (date range, project, task, tags, billable)
- Daily subtotals and grand total calculate correctly
- Filters persist in URL for bookmarking

---

### Task Group 8: Manual Time Entry Forms
**Dependencies:** Task Group 4

- [x] 8.0 Complete manual time entry create/edit forms
  - [x] 8.1 Write 2-8 focused tests for time entry forms
    - Limit to 2-8 highly focused tests maximum
    - Test only critical behaviors (three input modes work, validation works, form submission works)
    - Skip exhaustive testing of all form scenarios
  - [x] 8.2 Create time entry form template
    - Location: templates/time_tracking/time_entry_form.html
    - Fields: Task (required, dropdown/autocomplete), Start Time (datetime), End Time (datetime), Duration (duration input), Description (textarea), Tags (multi-select), Billable (checkbox), Billable Rate (decimal input), Currency (dropdown)
    - Follow existing form patterns from tasks/forms.py and templates
    - Use Tailwind CSS form styling consistent with existing forms
  - [x] 8.3 Implement intelligent mode switching
    - Use Alpine.js to detect which fields user fills first
    - Mode A: If user fills Start Time and End Time, calculate Duration (readonly)
    - Mode B: If user fills Start Time and Duration, calculate End Time (readonly)
    - Mode C: If user fills only Duration, leave Start Time and End Time null
    - Show/hide calculated fields dynamically based on mode
    - Allow switching between modes by clearing fields
  - [x] 8.4 Add client-side validation
    - Validate End Time > Start Time in Mode A
    - Validate Duration is positive in all modes
    - Validate required fields (Task, Duration or Start/End times)
    - Show inline validation errors using Alpine.js
    - Validation for UX only - server-side validation is authoritative
  - [x] 8.5 Implement task dropdown with project context
    - Populate task dropdown from user's accessible tasks
    - Optionally filter by selected project if project filter active
    - Show task name and project name in dropdown options
    - Use autocomplete/search for large task lists
    - Follow pattern from existing task selection UIs
  - [x] 8.6 Implement tags multi-select input
    - Multi-select dropdown or tag chips interface
    - Support creating new tags inline
    - Populate existing tags from user's time entries and tasks
    - Follow existing tag input patterns
  - [x] 8.7 Implement billable rate field with currency
    - Show billable rate and currency fields only when "Billable" checkbox checked
    - Pre-populate rate from task/project/user preferences (task > project > user default)
    - Allow manual override of rate
    - Currency dropdown with common options (USD, EUR, GBP, etc.)
    - Calculate and display estimated revenue below form (rate * duration)
  - [x] 8.8 Create TimeEntryForm Django form class
    - Location: time_tracking/forms.py
    - Implement clean() method for cross-field validation
    - Validate three input modes on server side
    - Validate end_time > start_time, positive duration
    - Apply time rounding rules from UserTimePreferences in clean()
    - Return user-friendly error messages
  - [x] 8.9 Implement inline edit for time entries in list view
    - Add "Edit" button on each time entry row
    - Show inline edit form (modal or expandable row) with pre-filled data
    - Submit via HTMX, update row on success without page reload
    - Follow HTMX partial update patterns from task views
  - [x] 8.10 Ensure time entry form tests pass
    - Run ONLY the 2-8 tests written in 8.1
    - Verify all three input modes work correctly
    - Verify form validation works
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 8.1 pass
- Time entry form supports all three input modes with intelligent switching
- Client-side and server-side validation work correctly
- Inline editing works in list view
- Billable rate and currency fields work correctly

---

### Task Group 9: Idle Time Detection and Celery Tasks
**Dependencies:** Task Groups 2-3

- [x] 9.0 Complete idle time detection system
  - [x] 9.1 Write 2-8 focused tests for idle detection logic
    - Limit to 2-8 highly focused tests maximum
    - Test only critical behaviors (idle threshold detection, notification sent, user actions apply correctly)
    - Skip exhaustive testing of all idle scenarios
  - [x] 9.2 Create Celery periodic task for idle detection
    - Location: time_tracking/tasks.py
    - Task name: check_idle_timers
    - Schedule: every 1 minute via Celery Beat
    - Logic: Query all active timers (is_running=True) from PostgreSQL
    - For each timer, check if (current_time - start_time) > idle_threshold_minutes from UserTimePreferences
    - If idle, create idle notification record and send notification to user
  - [x] 9.3 Create IdleTimeNotification model
    - Fields: user (FK to User), time_entry (FK to TimeEntry), idle_start_time (DateTimeField), notification_sent_at (DateTimeField), action_taken (CharField, choices: keep/discard/stop_at_idle/none, default 'none'), action_taken_at (DateTimeField, nullable), created_at
    - Indexes: user_id, time_entry_id, action_taken
    - One notification per timer idle event
  - [x] 9.4 Implement idle notification UI
    - Create notification component/modal in header (near timer widget)
    - Display: "You've been idle since [idle_start_time]. Current time: [current_time]."
    - Action buttons: Keep Time (no changes), Discard Idle Time (adjust end_time to idle_start_time), Stop Timer at Idle Start (stop timer, set end_time to idle_start_time)
    - Use Alpine.js modal for notification display
    - Notification auto-appears when idle detected (via WebSocket or polling)
  - [x] 9.5 Implement idle action endpoints
    - POST /api/timers/idle/keep/ - mark action as 'keep', no changes to timer
    - POST /api/timers/idle/discard/ - adjust timer's duration by removing idle time
    - POST /api/timers/idle/stop/ - stop timer, set end_time to idle_start_time
    - All endpoints require time_entry_id and notification_id
    - Update IdleTimeNotification.action_taken and action_taken_at
    - Update TimeEntry accordingly (adjust end_time or duration)
    - Clear idle notification from UI after action taken
  - [x] 9.6 Implement idle time calculation logic
    - Calculate idle duration: current_time - idle_start_time
    - Discard Idle Time action: new_duration = (idle_start_time - start_time)
    - Stop Timer at Idle Start action: set end_time = idle_start_time, recalculate duration
    - Apply time rounding rules after adjustment
    - Update TimeEntry in database and Redis cache
  - [x] 9.7 Add idle detection configuration in UserTimePreferences
    - Field: idle_threshold_minutes (default: 5 minutes)
    - Provide UI in user settings to configure threshold
    - Validate threshold must be >= 1 minute
    - Option to disable idle detection (set threshold to 0 or null)
  - [x] 9.8 Ensure idle detection tests pass
    - Run ONLY the 2-8 tests written in 9.1
    - Verify Celery task detects idle timers
    - Verify notification sent and actions work
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 9.1 pass
- Celery periodic task runs every 1 minute and detects idle timers
- Idle notification appears in UI when idle detected
- All idle actions (keep/discard/stop) work correctly
- Idle threshold configurable in user preferences

---


### Task Group 10: Advanced Features (Pomodoro, Rounding, Suggestions)
**Dependencies:** Task Groups 2-4

- [x] 10.0 Complete advanced time tracking features
  - [x] 10.1 Write 2-8 focused tests for advanced features
    - Limit to 2-8 highly focused tests maximum
    - Test only critical behaviors (Pomodoro session tracking, time rounding, suggestion generation)
    - Skip exhaustive testing of all advanced feature scenarios
  - [x] 10.2 Implement Pomodoro timer mode
    - Add "Pomodoro Mode" checkbox when starting timer
    - When enabled, create PomodoroSession record on timer start
    - Use WebSocket or JavaScript timer to track 25-minute work intervals
    - Show Pomodoro progress indicator in timer widget (e.g., "1/4 Pomodoros")
    - Send notification when work interval completes
    - Option to auto-start break timer or skip break
    - Mark session as completed when full interval finished
  - [x] 10.3 Create Pomodoro notification and break timer
    - Audio/visual notification when 25-minute work interval completes
    - Modal dialog: "Pomodoro complete! Take a 5-minute break?"
    - Buttons: Start Break (start 5-min break timer), Skip Break (continue working)
    - If break started, show break countdown in timer widget
    - After break, prompt to start next Pomodoro or continue regular timer
  - [x] 10.4 Implement time rounding logic
    - Create TimeRounding service class in time_tracking/services/rounding.py
    - Methods: round_duration(duration, interval, method)
    - Intervals: 5, 10, 15, 30 minutes (from UserTimePreferences)
    - Methods: 'up' (always round up), 'down' (always round down), 'nearest' (round to nearest interval)
    - Apply rounding when stopping timer and on manual entry save
    - Show both actual and rounded duration in confirmation before save
    - Allow user to override rounded value before final save
  - [x] 10.5 Implement automatic time suggestions
    - Create TimeSuggestion service class in time_tracking/services/suggestions.py
    - Method: get_suggestion(user, task, context) - returns suggested duration
    - Analyze historical time entries for same task or similar tasks (by name, project, tags)
    - Calculate average or median duration from historical entries
    - Require minimum 3 historical entries before showing suggestion
    - Consider time-of-day patterns (morning vs. afternoon entries)
    - Cache suggestions in Redis for performance
  - [x] 10.6 Display time suggestions in manual entry form
    - Show suggestion as placeholder or hint text in Duration field
    - Format: "Suggested: 1h 30m (based on X previous entries)"
    - User can accept suggestion with one click (populate Duration field)
    - User can manually override suggestion
    - Update suggestion when task selection changes
  - [x] 10.7 Implement time goals and budgets
    - Create time goal form: target_duration, goal_type (daily/weekly/monthly/total), project or task, start/end dates
    - Display progress bars in dashboard and project/task detail pages
    - Calculate progress: (actual_time_spent / target_duration) * 100
    - Show warning indicators: 80% (yellow), 100% (orange), 120%+ (red)
    - Support multiple concurrent goals with different scopes
  - [x] 10.8 Implement billable rates and revenue tracking
    - Rate precedence: task.billable_rate > project.billable_rate > user.default_billable_rate
    - Calculate revenue when creating/updating time entry: duration * applicable_rate
    - Store rate with time entry for historical accuracy
    - Display revenue column in time entries list (only for billable entries)
    - Calculate total revenue in list view totals and reports
  - [x] 10.9 Ensure advanced features tests pass
    - Run ONLY the 2-8 tests written in 10.1
    - Verify Pomodoro mode works correctly
    - Verify time rounding applies correctly
    - Verify suggestions generate correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 10.1 pass
- Pomodoro timer mode works with notifications and break tracking
- Time rounding applies correctly based on user preferences
- Automatic time suggestions work based on historical data
- Time goals/budgets track progress with warning indicators
- Billable rates and revenue calculate correctly
---

### Task Group 11: WebSocket Integration for Live Updates
**Dependencies:** Task Groups 2-3, 5

- [x] 11.0 Complete WebSocket integration for real-time timer updates
  - [x] 11.1 Write 2-8 focused tests for WebSocket functionality
    - Limit to 2-8 highly focused tests maximum
    - Test only critical behaviors (WebSocket connection, timer updates broadcast, cross-tab synchronization)
    - Skip exhaustive testing of all WebSocket scenarios
  - [x] 11.2 Create TimerConsumer for Django Channels
    - Location: time_tracking/consumers.py
    - Consumer type: AsyncWebsocketConsumer
    - Handle connections: add user to personal timer channel group
    - Handle disconnections: remove user from channel group
    - Channel group name: "timer_{user_id}"
  - [x] 11.3 Implement WebSocket message handlers
    - Message type: "timer.started" - broadcast when timer started
    - Message type: "timer.stopped" - broadcast when timer stopped
    - Message type: "timer.updated" - broadcast when timer description updated
    - Message type: "timer.discarded" - broadcast when timer discarded
    - Include full timer data in message payload (task, project, elapsed_time, etc.)
  - [x] 11.4 Update timer API endpoints to broadcast via WebSocket
    - In TimerViewSet.start(), send "timer.started" message to user's channel group
    - In TimerViewSet.stop(), send "timer.stopped" message to user's channel group
    - In TimerViewSet.discard(), send "timer.discarded" message to user's channel group
    - Use Django Channels' channel_layer.group_send()
  - [x] 11.5 Implement WebSocket client in timer widget
    - Connect to WebSocket on page load: ws://domain/ws/timer/
    - Listen for "timer.started", "timer.stopped", "timer.updated", "timer.discarded" messages
    - Update Alpine.js timer widget state when messages received
    - Handle reconnection on connection loss
    - Show connection status indicator (optional)
  - [x] 11.6 Implement cross-tab synchronization
    - When timer started in one tab, all other tabs update to show new timer
    - When timer stopped in one tab, all other tabs update to hide timer widget
    - When timer discarded in one tab, all other tabs update accordingly
    - Ensure timer countdown stays synchronized across tabs
  - [x] 11.7 Configure WebSocket routing
    - Location: workstate/routing.py (or time_tracking/routing.py)
    - Add TimerConsumer to URL routing: path("ws/timer/", TimerConsumer.as_asgi())
    - Update asgi.py to include WebSocket routing
    - Configure Django Channels in settings.py with Redis channel layer
  - [x] 11.8 Ensure WebSocket tests pass
    - Run ONLY the 2-8 tests written in 11.1
    - Verify WebSocket connection works
    - Verify messages broadcast correctly
    - Verify cross-tab synchronization works
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 11.1 pass
- WebSocket connection established for authenticated users
- Timer updates broadcast to all user's connected tabs
- Cross-tab synchronization works correctly
- Timer widget updates in real-time via WebSocket

---

### Task Group 12: Reporting and Analytics Dashboard
**Dependencies:** Task Groups 4, 7, 10

- [x] 12.0 Complete reporting and analytics dashboard
  - [x] 12.1 Write 2-8 focused tests for analytics calculations
    - Limit to 2-8 highly focused tests maximum
    - Test only critical calculations (total hours, billable hours, revenue, time-of-day patterns)
    - Skip exhaustive testing of all analytics scenarios
  - [x] 12.2 Create analytics dashboard page template
    - Location: templates/time_tracking/analytics_dashboard.html
    - Layout: Summary cards at top (today, this week, this month), charts below, detailed breakdowns
    - Use responsive grid layout with Tailwind CSS
    - Follow existing dashboard patterns from accounts/dashboard_views.py
  - [x] 12.3 Implement summary statistics calculations
    - Total hours today: sum duration where date = today
    - Total hours this week: sum duration where date in current week
    - Total hours this month: sum duration where date in current month
    - Billable vs. non-billable hours comparison for each period
    - Total revenue for each period (sum of duration * billable_rate for billable entries)
    - Display in summary cards with icons and formatted values
  - [x] 12.4 Implement project breakdown chart
    - Calculate time spent per project in selected date range
    - Display as pie chart or bar chart
    - Use Chart.js or similar library for visualization
    - Show project name and total duration for each project
    - Interactive: click project to filter detailed view
  - [x] 12.5 Implement task breakdown chart
    - Calculate time spent per task in selected date range
    - Display as horizontal bar chart (sorted by duration DESC)
    - Show top 10 tasks by time spent
    - Include "View All" link to detailed task report
  - [x] 12.6 Implement tag breakdown chart
    - Calculate time spent per tag in selected date range
    - Display as tag cloud or bar chart
    - Show tag name and total duration for each tag
    - Interactive: click tag to filter detailed view
  - [x] 12.7 Implement time-of-day heatmap
    - Calculate time entries by hour of day (0-23)
    - Display as heatmap with color intensity based on hours logged
    - Show which hours user is most productive
    - Group by hour across all days in selected date range
  - [x] 12.8 Implement day-of-week patterns analysis
    - Calculate time entries by day of week (Monday-Sunday)
    - Display as bar chart showing average hours per weekday
    - Show which days user is most productive
    - Compare billable vs. non-billable hours per day
  - [x] 12.9 Implement export functionality
    - Export to CSV: all time entries in current filtered view with all columns
    - Export to PDF: formatted report with summary statistics and charts
    - Export to Excel: detailed spreadsheet with multiple sheets (summary, by project, by task, by tag)
    - Use Django library (e.g., reportlab for PDF, openpyxl for Excel)
    - Download links/buttons in analytics dashboard
  - [x] 12.10 Add date range selector for analytics
    - Date range picker: Start Date and End Date
    - Quick filters: Today, This Week, This Month, Last Month, Last 3 Months, This Year
    - Update all analytics calculations and charts when date range changed
    - Use HTMX to update dashboard without full page reload
  - [x] 12.11 Ensure analytics tests pass
    - Run ONLY the 2-8 tests written in 12.1
    - Verify summary statistics calculate correctly
    - Verify charts display correct data
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 12.1 pass
- Summary statistics calculate correctly for today/week/month
- All charts display correct data and are interactive
- Time-of-day heatmap and day-of-week patterns show correctly
- Export to CSV/PDF/Excel works correctly
- Date range selector updates all analytics

---

### Task Group 13: User Settings and Preferences UI
**Dependencies:** Task Groups 1, 9, 10

- [x] 13.0 Complete user settings for time tracking preferences
  - [x] 13.1 Write 2-8 focused tests for settings form
    - Limit to 2-8 highly focused tests maximum
    - Test only critical behaviors (preferences save correctly, validation works, defaults set correctly)
    - Skip exhaustive testing of all settings scenarios
  - [x] 13.2 Create time tracking settings page template
    - Location: templates/time_tracking/settings.html
    - Sections: Time Rounding, Idle Detection, Pomodoro Timer, Billable Rates, General Preferences
    - Use form layout with clear section headers and help text
    - Follow existing settings page patterns
  - [x] 13.3 Implement time rounding settings form
    - Rounding interval: Radio buttons or dropdown (Off, 5 min, 10 min, 15 min, 30 min)
    - Rounding method: Radio buttons (Round Up, Round Down, Round to Nearest)
    - Show examples of rounding behavior for each combination
    - Default: Off (no rounding)
  - [x] 13.4 Implement idle detection settings form
    - Idle threshold: Number input (minutes, default: 5)
    - Enable/disable idle detection: Checkbox
    - Help text explaining idle detection behavior
    - Validation: threshold must be >= 1 minute if enabled
  - [x] 13.5 Implement Pomodoro timer settings form
    - Work interval duration: Number input (minutes, default: 25)
    - Break interval duration: Number input (minutes, default: 5)
    - Auto-start breaks: Checkbox (default: unchecked)
    - Help text explaining Pomodoro technique
    - Validation: work interval must be >= 5 minutes, break interval >= 1 minute
  - [x] 13.6 Implement billable rates settings form
    - Default billable rate: Decimal input (hourly rate, optional)
    - Default currency: Dropdown (USD, EUR, GBP, etc., default: USD)
    - Help text explaining rate precedence (task > project > user default)
    - Validation: rate must be >= 0 if provided
  - [x] 13.7 Create UserTimePreferencesForm Django form
    - Location: time_tracking/forms.py
    - All fields from UserTimePreferences model
    - Implement clean() methods for validation
    - Return user-friendly error messages
  - [x] 13.8 Implement settings save endpoint
    - POST /time_tracking/settings/ - create or update UserTimePreferences
    - Get or create UserTimePreferences instance for current user
    - Update all fields from form data
    - Return success message and redirect back to settings page
    - Show inline success/error messages
  - [x] 13.9 Ensure settings form tests pass
    - Run ONLY the 2-8 tests written in 13.1
    - Verify preferences save correctly
    - Verify validation works
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 13.1 pass
- Settings page displays all preference options
- Form validation works correctly
- Preferences save and apply to timer behavior
- Default values set correctly for new users

---

### Task Group 14: Navigation and URL Routing
**Dependencies:** All previous task groups

- [x] 14.0 Complete navigation and URL structure
  - [x] 14.1 Write 2-8 focused tests for navigation and routing
    - Limit to 2-8 highly focused tests maximum
    - Test only critical URLs (list view, form views, dashboard, settings accessible)
    - Skip exhaustive testing of all URL patterns
  - [x] 14.2 Configure URL routing for time tracking app
    - Location: time_tracking/urls.py
    - Patterns: /time/ (list view), /time/new/ (create entry), /time/<id>/edit/ (edit entry), /time/<id>/delete/ (delete entry), /time/analytics/ (dashboard), /time/settings/ (preferences)
    - API patterns: /api/timers/start/, /api/timers/stop/, /api/timers/active/, /api/timers/discard/, /api/time-entries/ (CRUD)
    - Include URL patterns in main workstate/urls.py
  - [x] 14.3 Add time tracking links to main navigation
    - Location: templates/base.html or templates/components/nav.html
    - Add "Time Tracking" menu item in main sidebar/header navigation
    - Sub-items: Time Entries (list), New Entry (create), Analytics (dashboard), Settings (preferences)
    - Highlight active menu item based on current URL
    - Follow existing navigation patterns
  - [x] 14.4 Create navigation breadcrumbs for time tracking pages
    - Show breadcrumbs: Home > Time Tracking > [Current Page]
    - Display in page header area
    - Follow existing breadcrumb patterns
  - [x] 14.5 Implement URL name-based navigation
    - Use Django's URL naming (e.g., 'time_entry_list', 'time_entry_create')
    - Update all links to use {% url %} template tag
    - Ensure consistent naming across views and templates
  - [x] 14.6 Ensure navigation tests pass
    - Run ONLY the 2-8 tests written in 14.1
    - Verify all URLs resolve correctly
    - Verify navigation links work
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 14.1 pass
- All time tracking URLs configured and resolve correctly
- Time tracking menu items appear in main navigation
- Breadcrumbs show correct navigation path
- All links use named URLs for maintainability

---

### Task Group 15: Final Integration and Comprehensive Testing
**Dependencies:** All previous task groups

- [x] 15.0 Complete final integration and comprehensive testing
  - [x] 15.1 Review existing tests from all previous task groups
    - Review tests from Task Groups 1-14 (approximately 28-112 tests total)
    - Identify which critical user workflows are already covered
    - Document test coverage gaps specific to time tracking feature
  - [x] 15.2 Analyze test coverage gaps for time tracking feature only
    - Identify critical end-to-end workflows that lack test coverage
    - Focus ONLY on gaps related to time tracking requirements
    - Do NOT assess entire application test coverage
    - Priority workflows: Start timer -> stop timer -> view in list, Manual entry all three modes -> view in list, Idle detection workflow, Filter time entries by multiple criteria
  - [x] 15.3 Write up to 10 additional strategic tests maximum
    - Add maximum of 10 new integration/end-to-end tests to fill identified critical gaps
    - Focus on integration points: timer <-> database <-> cache, API <-> WebSocket, forms <-> validation
    - Focus on end-to-end workflows: complete timer lifecycle, complete manual entry lifecycle, complete filter workflow
    - Do NOT write comprehensive coverage for all scenarios
    - Skip edge cases, performance tests, and accessibility tests unless business-critical
  - [x] 15.4 Run feature-specific tests only
    - Run ONLY tests related to time tracking feature (from all task groups)
    - Expected total: approximately 38-122 tests maximum
    - Do NOT run the entire application test suite
    - Verify all critical workflows pass
    - Fix any failing tests
  - [x] 15.5 Perform manual integration testing
    - Test complete timer workflow: start -> edit description -> stop -> view in list
    - Test manual entry workflow: create with all three modes -> edit -> delete
    - Test filters: apply multiple filters -> verify results -> clear filters
    - Test idle detection: start timer -> wait for idle threshold -> handle notification
    - Test Pomodoro: start Pomodoro timer -> complete interval -> take break
    - Test cross-tab sync: open in two tabs -> start/stop timer in one -> verify other tab updates
  - [x] 15.6 Verify integration with existing code
    - Verify timer buttons appear correctly on task cards, detail, and list views
    - Verify task -> time entry linking works correctly
    - Verify project inheritance from task works correctly
    - Verify dashboard widgets integrate properly
    - Verify no conflicts with existing models, views, or templates
  - [x] 15.7 Performance optimization review
    - Review database queries for N+1 problems (use select_related/prefetch_related)
    - Review Redis cache usage for active timers
    - Review WebSocket message frequency and payload size
    - Review Celery task performance (idle detection)
    - Optimize slow queries if necessary
  - [x] 15.8 Security review
    - Verify authorization: users can only access own timers and time entries
    - Verify validation: all inputs validated on server side
    - Verify CSRF protection on all forms
    - Verify WebSocket authentication
    - Verify no sensitive data exposed in API responses or WebSocket messages
  - [x] 15.9 Documentation review
    - Review code comments for clarity
    - Document any non-obvious business logic
    - Document API endpoints (if API docs required)
    - Document WebSocket message format
    - Update CLAUDE.md or similar project docs if needed

**Acceptance Criteria:**
- All feature-specific tests pass (approximately 38-122 tests total)
- No more than 10 additional tests added when filling in testing gaps
- All critical user workflows tested and working
- Manual integration testing completed successfully
- Integration with existing code verified
- Performance and security reviews completed
- No regressions in existing functionality

---

## Execution Order

Recommended implementation sequence:

1. **Foundation (Task Groups 1-2):** Database models and Redis cache layer - establishes data structure
2. **Core Timer API (Task Group 3):** Timer start/stop/discard endpoints - core functionality
3. **Manual Entry API (Task Group 4):** Time entry CRUD operations - alternative input method
4. **Timer UI (Task Groups 5-6):** Header widget and task UI buttons - user interface for timer
5. **List and Filters (Task Groups 7-8):** Time entries list view and manual entry forms - viewing and editing
6. **Advanced Features Part 1 (Task Group 9):** Idle detection - Celery integration
7. **Advanced Features Part 2 (Task Group 10):** Pomodoro, rounding, suggestions - enhancing UX
8. **Real-time Updates (Task Group 11):** WebSocket integration - cross-tab sync
9. **Analytics (Task Group 12):** Reporting dashboard - insights and exports
10. **Settings (Task Group 13):** User preferences UI - customization
11. **Navigation (Task Group 14):** URL routing and menu items - discoverability
12. **Final Integration (Task Group 15):** Comprehensive testing and optimization - polish

## Important Implementation Notes

### Testing Philosophy
- Each task group (1-14) writes 2-8 focused tests covering ONLY critical behaviors
- Task Group 15 adds maximum 10 additional tests to fill critical gaps
- Total expected tests: approximately 38-122 tests for entire feature
- Focus on behavior, not implementation details
- Run only feature-specific tests, not entire application suite

### Integration Points with Existing Code
- **Task model:** Foreign key relationship, inherit project from task
- **Dashboard:** Add time tracking summary widgets using existing dashboard patterns
- **Navigation:** Add time tracking menu items to existing sidebar/header
- **Forms:** Follow validation patterns from tasks/forms.py
- **Templates:** Use Tailwind CSS classes and component patterns from existing templates
- **HTMX:** Apply partial update patterns from task views
- **Alpine.js:** Use for timer countdown and modal components

### Technology Stack Alignment
- Django 5.x models with created_at/updated_at timestamps
- PostgreSQL constraints for data integrity
- Redis for active timer caching
- Celery for background tasks (idle detection, cache sync)
- Django Channels + WebSocket for real-time updates
- HTMX for dynamic UI updates without SPA
- Alpine.js for client-side reactivity
- Tailwind CSS for consistent styling

### Security and Validation
- Server-side validation is authoritative (client-side for UX only)
- User can only access own timers and time entries (permission checks in all endpoints)
- CSRF protection on all forms
- WebSocket authentication required
- No sensitive data in API responses or WebSocket messages

### Performance Considerations
- Redis cache for active timer state (fast retrieval, reduced DB load)
- Database indexes on foreign keys and frequently queried fields
- Query optimization with select_related/prefetch_related
- WebSocket for efficient real-time updates (avoid polling)
- Celery for background processing (don't block request/response cycle)

### Business Rules to Enforce
- Single active timer per user (database constraint + application logic)
- Timer must always be linked to a task (no standalone timers)
- Time rounding rules apply on timer stop and manual entry save
- Billable rate precedence: task > project > user default
- Idle detection only for active timers (not manual entries)
- Confirmation dialogs for destructive actions (discard timer, auto-stop previous timer)

---

## Task Group Dependencies Visualization

```
Group 1 (Models) ─┬─> Group 2 (Redis Cache) ──> Group 3 (Timer API) ──┬─> Group 5 (Header Widget) ─> Group 11 (WebSocket)
                  │                                                     │
                  │                                                     └─> Group 6 (Task UI Buttons)
                  │
                  └─> Group 4 (Manual Entry API) ──┬─> Group 7 (List & Filters) ─┬─> Group 12 (Analytics)
                                                    │                             │
                                                    └─> Group 8 (Entry Forms) ────┘

Group 3 + 2 ──> Group 9 (Idle Detection)

Groups 2-4 ──> Group 10 (Advanced Features)

Group 1 + 9 + 10 ──> Group 13 (Settings)

All Groups ──> Group 14 (Navigation) ──> Group 15 (Final Testing)
```
