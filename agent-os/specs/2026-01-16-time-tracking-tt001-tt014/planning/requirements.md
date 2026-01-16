# Spec Requirements: Time Tracking (TT001-TT014)

## Initial Description
Time Tracking (TT001-TT014) - Real-time timer with start/stop functionality, manual time entry with start/end times or duration-only mode, running timer display in header across all views, timer description and project/task linking, discard timer capability, and complete time entry CRUD with list view and filters. Foundation for productivity tracking and reporting.

## Requirements Discussion

### First Round Questions

**Q1: Timer Concurrency - Should the system allow only one active timer per user, or support multiple concurrent timers?**
**Answer:** Single active timer per user. Automatically stop the previous timer when starting a new one.

**Q2: Manual Entry Modes - For manual time entries, which input modes should be supported?**
**Answer:** Support all three modes:
- (a) Start time + End time (calculates duration)
- (b) Start time + Duration (calculates end time)
- (c) Duration only (no specific start/end times)

**Q3: Header Display - What should the running timer display in the header show?**
**Answer:** Full featured display including:
- Elapsed time (live updating)
- Task name
- Stop button
- Quick edit/description button

**Q4: Timer Linking - Should users be able to start timers without task association, or must timers always be linked to a task?**
**Answer:** Auto-link from tasks only. No timers without task association.

**Q5: Discard Confirmation - When discarding a running timer, should there be a confirmation dialog?**
**Answer:** Always show confirmation dialog to prevent accidental data loss.

**Q6: List View Defaults - What default time range views should be provided in the time entries list?**
**Answer:** Offer multiple default views:
- Current week
- Last 7 days
- Last 30 days

**Q7: Filters - Which filters should be available for the time entries list?**
**Answer:** Include ALL filters:
- Date range (custom)
- Project
- Task
- Tags
- Billable/non-billable status

**Q8: Scope - Should this implementation include advanced features or focus on core functionality?**
**Answer:** COMPREHENSIVE implementation including:
- Idle time detection
- Automatic time suggestions
- Time rounding rules
- Pomodoro timer integration
- Time goals/budgets
- Billable rates
- Advanced reporting/analytics

### Existing Code to Reference

**Similar Features Identified:**
- Feature: Existing Workstate task management UI - Patterns to reference for task UI, dashboard layouts, CRUD operations, and model structures
- Components to potentially reuse: Task UI components, dashboard widgets, form patterns
- Backend logic to reference: Existing model patterns, CRUD operations, validation logic

### Follow-up Questions
No follow-up questions were necessary based on comprehensive initial answers.

## Visual Assets

### Files Provided:
No visual assets provided.

### Visual Insights:
User prefers to follow existing Workstate design system and patterns established in the codebase.

## Requirements Summary

### Functional Requirements

**Core Timer Functionality:**
- Start/stop timer associated with a task
- Single active timer per user (auto-stop previous when starting new)
- Live elapsed time display
- Timer must always be linked to a task (no standalone timers)
- Discard timer with confirmation dialog
- Quick edit timer description while running

**Manual Time Entry:**
- Three input modes:
  - Start time + End time (auto-calculate duration)
  - Start time + Duration (auto-calculate end time)
  - Duration only (no specific timestamps)
- Full CRUD operations for time entries
- Support for task/project association
- Tag support for categorization
- Billable/non-billable flag

**Header Display:**
- Persistent running timer widget visible across all views
- Shows: elapsed time (live), task name, stop button, quick edit button
- Minimal but functional UI that doesn't obstruct content

**Time Entries List View:**
- Default view options: current week, last 7 days, last 30 days
- Custom date range filter
- Filter by: project, task, tags, billable status
- Display: task name, project, duration, start/end times, description, billable status
- Inline editing capability
- Bulk operations (delete, update billable status, etc.)

**Advanced Features:**
- Idle time detection with notifications
- Automatic time suggestions based on activity
- Time rounding rules (configurable: nearest 5/10/15/30 min)
- Pomodoro timer integration (25/5 min intervals)
- Time goals/budgets per project or task
- Billable rates configuration
- Advanced reporting and analytics

**Data Tracking:**
- Start timestamp
- End timestamp
- Duration (calculated or manual)
- Task association (required)
- Project association (inherited from task)
- Description/notes
- Tags
- Billable flag
- Billable rate (optional)
- Created/updated timestamps

### Reusability Opportunities
- Existing Workstate task UI patterns for consistent interface
- Dashboard widget patterns for header timer display
- CRUD operation patterns from existing task management
- Model structure patterns (timestamps, validation, constraints)
- Form validation patterns
- API endpoint patterns from Django REST Framework setup

### Scope Boundaries

**In Scope:**
- Real-time timer start/stop with task association
- Manual time entry with three input modes
- Persistent header timer display
- Time entry CRUD operations
- List view with multiple filters and default ranges
- Idle time detection
- Automatic time suggestions
- Time rounding rules
- Pomodoro timer integration
- Time goals and budgets
- Billable rates and status
- Advanced reporting and analytics
- Single active timer enforcement
- Timer discard with confirmation

**Out of Scope:**
- Multiple concurrent timers per user
- Standalone timers without task association
- Time tracking for team members (viewing/managing others' time)
- Invoice generation (may be future enhancement)
- Third-party calendar integration (separate feature)
- Mobile app timer sync (separate platform feature)
- Offline timer support (requires separate implementation)

### Technical Considerations

**Integration Points:**
- Task model (timer must link to existing task)
- Project model (inherited from task)
- Tag system (for categorization)
- User authentication (timer ownership)
- WebSocket/Channels for live timer updates
- Celery for idle time detection background jobs
- Dashboard header component integration

**Existing System Constraints:**
- Must follow Django model patterns with created_at/updated_at
- Must use Django REST Framework for API endpoints
- Must use HTMX for dynamic UI updates
- Must use Alpine.js for client-side timer countdown
- Must follow Tailwind CSS for styling
- Must support PostgreSQL database constraints
- Must follow existing validation patterns (model + database layers)

**Technology Preferences:**
- Python/Django backend
- PostgreSQL for data storage
- Redis for caching active timer state
- HTMX for dynamic UI updates
- Alpine.js for timer countdown and client-side state
- Tailwind CSS for consistent styling
- Django Channels for real-time timer updates

**Similar Code Patterns to Follow:**
- Task CRUD operations and model structure
- Dashboard widget patterns
- Form validation and error handling
- API endpoint structure and response formats
- Database migration patterns
- Test structure for models, views, and API endpoints
