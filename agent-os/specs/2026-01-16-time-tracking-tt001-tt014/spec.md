# Specification: Time Tracking (TT001-TT014)

## Goal
Build a comprehensive time tracking system with real-time timer functionality, manual time entry support, persistent header display, and advanced features including idle detection, Pomodoro integration, time rounding, billable rates, and analytics. The system must enforce single active timer per user and ensure all time entries are linked to tasks.

## User Stories
- As a user, I want to start and stop a timer linked to a task so that I can accurately track time spent on work without manual calculation
- As a user, I want to see my running timer in the header across all pages so that I'm always aware of active time tracking
- As a user, I want to manually log time using different input modes (start/end times, start/duration, or duration-only) so that I can record time flexibly based on how I remember it

## Specific Requirements

**Single Active Timer Enforcement**
- System must allow only one active timer per user at any time
- When starting a new timer, automatically stop any currently running timer
- Display confirmation dialog before auto-stopping with options to save or discard the previous timer
- Store active timer state in Redis for fast retrieval and real-time updates
- Fallback to PostgreSQL if Redis is unavailable to ensure timer persistence

**Timer Start/Stop from Tasks**
- Add "Start Timer" button to task cards, task detail pages, and task list views
- Timer must always be linked to a task - no standalone timers allowed
- Timer button should show "Stop Timer" state when task's timer is active
- Support optional description/notes field when starting timer for additional context
- Validate task exists and user has access before allowing timer start

**Persistent Header Timer Display**
- Display running timer widget in application header visible on all authenticated pages
- Show elapsed time updating every second using Alpine.js client-side countdown
- Display task name, project name (inherited from task), and timer description
- Include Stop button and Quick Edit button for description updates
- Widget should collapse to icon-only mode on mobile devices for space efficiency
- Use WebSocket connection (Django Channels) for cross-tab timer synchronization

**Manual Time Entry - Three Input Modes**
- Mode A: Start time + End time (system calculates duration automatically)
- Mode B: Start time + Duration (system calculates end time automatically)
- Mode C: Duration only (no specific start/end timestamps recorded)
- Form should intelligently switch between modes based on which fields user fills first
- Validate that start time is before end time in Mode A
- All modes must link to a task and support optional description, tags, and billable flag

**Timer Discard Functionality**
- Provide "Discard Timer" option in header timer widget and timer edit interfaces
- Always show confirmation dialog with clear warning about data loss
- Confirmation should display elapsed time being discarded
- After discard, clear timer from Redis and database without creating time entry record

**Time Entries List View with Default Ranges**
- Provide quick filter buttons: Current Week, Last 7 Days, Last 30 Days
- Current Week should show Monday-Sunday of current calendar week
- Default view should be Current Week on initial page load
- Display time entries in reverse chronological order (newest first)
- Show daily subtotals with total duration per day
- Show weekly/monthly grand totals based on active filter

**Comprehensive Filtering System**
- Custom date range filter with start and end date pickers
- Project filter dropdown populated from user's accessible projects
- Task filter dropdown (optionally filtered by selected project)
- Tags multi-select filter supporting multiple tag selection
- Billable status filter: All, Billable Only, Non-billable Only
- Filters should persist in URL query parameters for bookmarking and sharing

**Idle Time Detection**
- Detect user idle time after configurable threshold (default: 5 minutes)
- Show notification dialog asking user to adjust timer or mark time as inactive
- Notification should show idle start time and current time for reference
- Provide options: Keep time, Discard idle time, Stop timer at idle start
- Use Celery background task to check for idle timers every 1 minute
- Idle detection only applies to active timers, not manual entries

**Automatic Time Suggestions**
- Analyze historical time entries to suggest durations for similar tasks
- Suggestions based on task name, project, tags, and time of day patterns
- Display suggestion as placeholder or hint in manual entry form
- User can accept suggestion with one click or manually override
- Minimum 3 historical entries required before showing suggestions
- Cache suggestions in Redis for performance

**Time Rounding Rules**
- Support configurable rounding intervals: 5, 10, 15, 30 minutes
- Rounding rules apply when stopping timer or on manual entry
- Options: Round up, Round down, Round to nearest
- User can override rounded value before final save
- Rounding preference stored in user settings
- Display both actual and rounded time during confirmation

**Pomodoro Timer Integration**
- Provide Pomodoro mode option when starting timer (default: 25 min work, 5 min break)
- Show visual indicator and countdown for Pomodoro intervals
- Audio/visual notification when work interval completes
- Option to auto-start break timer or skip break
- Track Pomodoro sessions completed per task for productivity metrics
- Configurable work/break intervals in user preferences

**Time Goals and Budgets**
- Set time budgets per project or per task (e.g., "10 hours for Project A")
- Display progress bars showing time spent vs. budgeted time
- Warning indicators when approaching or exceeding budget (80%, 100%, 120% thresholds)
- Goals can be daily, weekly, monthly, or total for entire project/task lifecycle
- Support multiple concurrent goals with different scopes

**Billable Rates and Revenue Tracking**
- Assign hourly billable rates per project, per task, or per user default
- Calculate revenue based on billable hours and applicable rate
- Support multiple currency options with user-configurable default
- Rate precedence: Task rate > Project rate > User default rate
- Display total revenue calculations in time entries list and reports
- Rates stored with time entry for historical accuracy even if rates change later

**Advanced Reporting and Analytics**
- Summary dashboard showing total hours today, this week, this month
- Breakdown by project, task, and tag with visual charts
- Billable vs. non-billable hours comparison
- Time of day heatmap showing when user is most productive
- Day-of-week patterns analysis
- Export reports to CSV, PDF, or Excel formats
- Date range selector for custom reporting periods

## Existing Code to Leverage

**Task Model and CRUD Patterns (`tasks/models.py`, `tasks/views/task_views.py`)**
- Reuse Task model structure for foreign key relationship to TimeEntry
- Follow existing model patterns: created_at/updated_at timestamps, custom managers, clean() validation
- Apply same permission checking pattern (workspace ownership via task_list)
- Use similar query optimization techniques: select_related, prefetch_related
- Follow task's soft-delete pattern for archiving old time entries if needed

**Dashboard and View Patterns (`accounts/dashboard_views.py`)**
- Leverage dashboard layout for time tracking summary widgets
- Follow workspace filtering patterns for scoping time entries to user's workspaces
- Apply same sidebar navigation approach for time tracking views
- Reuse query optimization patterns (annotate with aggregates in single query)

**Form Validation and Input Patterns (`tasks/forms.py`)**
- Follow TaskForm patterns for TimeEntryForm validation
- Apply same Tailwind CSS classes for consistent styling
- Use similar clean() methods for field-level and form-level validation
- Implement tag handling pattern for time entry tags

**HTMX Partial Updates (`tasks/views/task_views.py`, templates)**
- Apply toggle status pattern (TaskToggleStatusView) for start/stop timer actions
- Use partial template rendering for timer widget updates
- Follow HTMX trigger patterns (HX-Trigger headers) for cross-component updates
- Implement similar Alpine.js state management for timer countdown

**Template Components and Styling (`templates/tasks/`, `templates/base.html`)**
- Follow existing card component patterns for time entry display
- Use consistent Tailwind utility classes from task templates
- Apply same responsive design patterns from task list views
- Integrate timer widget into base.html header similar to messages container

## Out of Scope
- Multi-user timer management (viewing or controlling other users' timers)
- Team-wide time tracking dashboards aggregating all team members
- Invoice generation from billable time (separate invoicing feature)
- Integration with external calendar systems (Google Calendar, Outlook)
- Mobile app timer with offline support (requires separate platform implementation)
- Timer reminders or notifications on external devices
- Automatic screenshot capture during timer sessions
- GPS-based time tracking for location verification
- Integration with third-party time tracking APIs (Toggl, Harvest, etc.)
- Time approval workflows for managers/supervisors
