# Specification: Task Due Date Management

## Goal
Enable users to efficiently view, filter, and manage tasks based on their due dates through dedicated views (Today, Upcoming, Overdue, No Due Date) and quick date actions, with clear visual indicators for due date status.

## User Stories
- As a user, I want to see only tasks due today so I can focus on immediate priorities without being distracted by overdue or future tasks
- As a user, I want quick date action buttons to rapidly set due dates (Today, Tomorrow, Next Week, Clear) without manually picking dates
- As a user, I want color-coded labels on tasks so I can instantly identify overdue, due today, and upcoming tasks at a glance

## Specific Requirements

**Today View (Strict Filtering)**
- Display only tasks where due_date equals current date (today)
- Exclude all overdue tasks (due_date < today) from this view
- Exclude all completed tasks regardless of due date
- Show active tasks only with status='active' and due_date=today
- Add "Today" link to main navigation sidebar
- Support workspace filtering in combination with today filter
- Include task count badge showing number of tasks due today

**Upcoming View (Future Tasks)**
- Default view shows tasks due in next 7 days (tomorrow through day 7)
- Provide filter options for 14-day and 30-day ranges via query parameters or dropdown
- Exclude today's tasks (separate Today view handles these)
- Exclude completed tasks
- Add "Upcoming" link to main navigation sidebar
- Sort by due_date ascending (soonest deadlines first)
- Display days remaining or specific dates for clarity

**Overdue View (Past Due Tasks)**
- Filter tasks where due_date < today AND status != 'completed'
- Sort by due_date ascending (oldest/most overdue first)
- Add "Overdue" link to main navigation sidebar
- Highlight urgency with prominent visual treatment
- Show how many days overdue for each task
- Include task count badge showing total overdue tasks

**No Due Date View**
- Filter tasks where due_date IS NULL
- Show all active tasks without deadlines
- Accessible from navigation sidebar or filter dropdown
- Help users identify tasks that need due dates assigned
- Sort by created_at descending (newest first)

**Quick Date Action Buttons**
- "Today" button sets due_date to current date
- "Tomorrow" button sets due_date to tomorrow (current date + 1 day)
- "Next Week" button sets due_date to next Monday
- "Clear Due Date" button sets due_date to NULL
- Available in task edit modal/form
- Available as inline actions on task list hover or dropdown menu
- Support bulk operations when multiple tasks selected
- Use HTMX for inline updates without page refresh

**Visual Date Status Indicators**
- Red label for overdue tasks (due_date < today, status='active')
- Yellow/amber label for tasks due today (due_date = today, status='active')
- Green/neutral label for upcoming tasks (due_date > today)
- Gray label for tasks with no due date (due_date IS NULL)
- Use Tailwind CSS badge/label styles for consistent design
- Display label next to task title in all list views
- Include small calendar icon with label for clarity

**Navigation Integration**
- Add "Today", "Upcoming", "Overdue" links to main sidebar navigation
- Position below "All Tasks" link in sidebar hierarchy
- Add "No Due Date" link in sidebar or as secondary filter option
- Highlight active view in navigation with background color or bold text
- Preserve workspace filtering when switching between due date views
- Use URL query parameters for view state (e.g., ?view=today, ?view=upcoming&days=14)

**Combining Filters**
- Allow due date views to work with existing workspace filter
- Support tag filtering in combination with due date views
- Enable filtering by task_list within due date views
- Maintain filter state in URL query parameters
- Show active filters as dismissible badges above task list
- Provide "Clear All Filters" button when multiple filters applied

**Query Optimization**
- Use existing due_date index on tasks table
- Leverage existing status index for active/completed filtering
- Prefetch related data (task_list, workspace, tags) in queries
- Cache task counts for Today/Upcoming/Overdue badges
- Use select_related and prefetch_related to minimize database queries

**Mobile Responsiveness**
- Collapse quick date action buttons into dropdown menu on mobile
- Stack navigation links vertically in mobile sidebar
- Make date labels readable at small screen sizes
- Ensure touch targets for inline actions meet minimum size (44x44px)

## Visual Design

No visual assets provided. Follow existing UI patterns found in the codebase:

**Navigation Sidebar Pattern**
- Use existing sidebar structure from templates/includes/nav.html
- Match icon style and spacing of current navigation items
- Add calendar icon SVG for due date-related links
- Use Tailwind classes: text-gray-700, hover:bg-gray-100, rounded-md

**Task List Card Pattern**
- Extend existing task card template from templates/tasks/task_list.html
- Add date status label next to priority badge
- Use existing Tailwind badge classes with date-specific colors
- Maintain hover states and HTMX edit functionality

**Quick Action Buttons**
- Use inline-flex button group with border-gray-300 borders
- Match existing button styling from task forms
- Add on hover for inline actions, or display in dropdown menu
- Use HTMX attributes for instant updates: hx-post, hx-target, hx-swap

**Filter Badge Display**
- Follow existing tag filter badge pattern from task_list.html (lines 22-35)
- Use bg-blue-50 border-blue-200 for filter container
- Include dismiss (X) button to clear filter
- Stack multiple filter badges horizontally with flex-wrap

## Existing Code to Leverage

**Task Model Methods (tasks/models.py)**
- Use existing is_overdue() method (line 434) to check overdue status
- Use existing is_due_today() method (line 441) to check if due today
- Leverage TaskManager.overdue() queryset method (line 278) for overdue view
- Leverage TaskManager.due_today() queryset method (line 286) for today view
- Extend TaskManager with upcoming() and no_due_date() methods

**TaskListView Filtering Pattern (tasks/views.py)**
- Replicate workspace filtering logic from TaskListView.get_queryset() (lines 294-308)
- Follow tag filtering pattern using request.GET.get() for due date view parameter
- Reuse prefetch_related('tags') and select_related() optimization patterns
- Apply same user access control via task_list__workspace__owner filter

**Navigation Template Structure (templates/includes/nav.html)**
- Add due date view links using same HTML structure as existing nav items
- Use Alpine.js x-data for any dropdown interactions if needed
- Match icon SVG style and Tailwind classes from current sidebar links
- Position new links in logical hierarchy below main task navigation

**Task Form and Quick Actions (tasks/forms.py, tasks/views.py)**
- Extend TaskForm to include quick date action handlers in clean() method
- Use existing TaskUpdateView pattern for inline HTMX updates (lines 201-279)
- Follow form_valid() pattern to set due_date based on button clicked
- Return HX-Trigger header for UI updates after quick action (line 261)

**URL Patterns (tasks/urls.py)**
- Add new URL patterns for due date views following existing naming convention
- Use query parameters for view switching instead of separate URLs if preferred
- Follow app_name='tasks' namespace for reverse URL lookups
- Maintain consistent URL structure with workspace_id where applicable

## Out of Scope
- Recurring task due date logic (part of Task Scheduling feature)
- Time-of-day due times beyond existing due_time field (handled separately)
- Calendar grid view or month view integration (separate Calendar View feature)
- Email or push notification reminders for due dates (separate Notifications feature)
- Due date modification history or audit trail (separate Audit Log feature)
- Natural language date parsing (e.g., "in 3 days", "next Friday")
- Dependency-based due date calculations (blocked by other tasks)
- Auto-rescheduling or smart due date suggestions based on AI
- Gantt chart or timeline visualization of due dates
- Export of due date reports to CSV or PDF
