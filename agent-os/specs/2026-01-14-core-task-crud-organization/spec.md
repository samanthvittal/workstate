# Specification: Core Task CRUD & Organization

## Goal
Implement task creation and editing functionality that allows users to create and modify tasks organized within task lists and workspaces. Tasks belong to task lists, which belong to workspaces. Users can create, view, edit, and organize tasks with title, description, due date/time, and priority. The interface provides workspace switching, task list grouping, user profile menu, and uses HTMX for dynamic interactions.

## User Stories
- As a user, I want to create task lists within my workspaces so that I can organize different types of tasks
- As a user, I want to create tasks within task lists so that I can track my work in an organized manner
- As a user, I want to edit existing tasks in a modal overlay so that I can update details without losing context
- As a user, I want to stay on the form after saving so that I can quickly add or edit multiple tasks
- As a user, I want to switch between workspaces so that I can work with different clients or projects
- As a user, I want a user menu dropdown so that I can access my profile, preferences, and logout easily

## Specific Requirements

### Data Model & Organization

**TaskList Model**
- Create TaskList model with fields: name (CharField, max 255 chars, required), description (TextField, optional), workspace (ForeignKey to Workspace, CASCADE), created_by (ForeignKey to User, CASCADE), created_at, updated_at
- TaskList belongs to a Workspace (one-to-many relationship)
- Tasks belong to a TaskList (one-to-many relationship)
- Unique constraint: task list name is unique per workspace
- Add index on workspace foreign key for efficient querying
- Add default ordering by created_at descending

**Task Model Updates**
- Update Task model: replace workspace ForeignKey with task_list ForeignKey to TaskList
- Tasks now belong to a TaskList, which belongs to a Workspace (two-level hierarchy)
- Workspace can be accessed via task.task_list.workspace (no direct workspace field on Task)
- Update related_name to 'tasks' on TaskList relationship
- Create migration to add task_list field and migrate existing tasks to default task lists
- Add database constraint ensuring task_list is not null

**Workspace Hierarchy**
- Workspace → TaskLists (one-to-many) → Tasks (one-to-many)
- Each workspace can have multiple task lists
- Each task list can have multiple tasks
- Deleting a workspace cascades to task lists and tasks
- Deleting a task list cascades to tasks only

### Task & TaskList Forms

**Task Creation Form**
- Render task creation form at `/workspace/<id>/tasklist/<id>/tasks/create/` using Django CreateView
- Display form fields: title (required, max 255 chars), description (optional textarea, markdown supported), due_date (optional date picker), due_time (optional time picker), priority (required, P1/P2/P3/P4 dropdown or buttons)
- Auto-focus on title field when form loads for quick task entry
- Use Tailwind CSS utility classes with clean, minimal design
- Validate that title is required and not only whitespace, due_time requires due_date, priority is one of P1/P2/P3/P4
- Associate task with current task list from URL parameter automatically
- Set created_by to request.user automatically in form_valid() method

**TaskList Creation Form**
- Render task list creation form at `/workspace/<id>/tasklists/create/` using Django CreateView
- Display form fields: name (required, max 255 chars), description (optional textarea)
- Auto-focus on name field when form loads
- Validate that name is required and not only whitespace
- Validate name is unique within the workspace
- Associate task list with current workspace from URL parameter automatically
- Set created_by to request.user automatically in form_valid() method

**Task Editing Form**
- Render task editing form at `/tasks/<id>/edit/` using Django UpdateView
- Load form in modal overlay using HTMX (hx-get, hx-target="#modal", hx-swap="innerHTML")
- Reuse same ModelForm as creation for DRY principle
- Pre-populate all fields with existing task data
- Allow users to toggle status between active and completed
- Validate workspace permission: user must own the workspace that contains the task

**Form Success Behavior**
- After successful save, display success message using Django messages framework
- Keep user on the same form (redirect back to form URL with success message)
- Reset form fields to empty for task creation (allows quick entry of multiple tasks)
- For task editing, close modal and update task display in background using HTMX out-of-band swap
- Show field-specific error messages inline below each field on validation failure

**Priority Display & Selection**
- Priority is required field with choices: P1 (Urgent/Red), P2 (High/Orange), P3 (Medium/Yellow), P4 (Low/Blue)
- Render priority selection as visual buttons with color indicators or styled dropdown
- Use Tailwind color classes: P1=red-600, P2=orange-600, P3=yellow-600, P4=blue-600
- Display priority badge on task with appropriate color and icon

**Due Date & Time Handling**
- Use HTML5 date input with Alpine.js enhancement for date picker
- Use HTML5 time input for due_time field
- Due_time field is hidden unless due_date has a value (Alpine.js conditional display)
- Validate that due_time cannot be set without due_date at both model and form level
- Allow past dates for flexibility (users may want to log overdue tasks)
- Display due date in user's preferred format from UserPreference model

**Description Field**
- Store description as plain text in TextField (max 10,000 characters)
- Render description as markdown in task display views using markdown library
- Use simple textarea input in forms without WYSIWYG editor
- Provide markdown formatting help text below field

**Workspace Integration**
- Determine current workspace from URL parameter for task creation
- Verify user has access to workspace using custom mixin (WorkspaceAccessMixin)
- Use LoginRequiredMixin for authentication on all task views
- Query tasks using Task.objects.for_workspace(workspace) manager method
- Use select_related('workspace', 'created_by') to avoid N+1 queries

**HTMX Dynamic Behavior**
- Use hx-get="/tasks/<id>/edit/" to load edit form in modal
- Use hx-post for form submission with hx-target and hx-swap directives
- Return partial HTML template for HTMX requests (check request.htmx in view)
- Use hx-swap="outerHTML" to replace task element after successful edit
- Use Alpine.js to control modal visibility (x-show directive with open state)

### Navigation & User Interface

**Navigation Bar**
- Display navigation bar on ALL pages including task creation, task list, and detail views
- Navigation bar must be consistent across all authenticated pages
- Extract navigation to reusable include template (templates/includes/nav.html)
- Include nav template in base.html or at the top of each page template
- Navigation structure: Logo/Workspace Selector (left), User Menu (right)

**Workspace Selector Dropdown**
- Position workspace dropdown next to "Workstate" logo at top left of navigation bar
- If user has only one workspace, display that workspace name as selected by default (no dropdown needed)
- If user has multiple workspaces, display dropdown with all workspaces
- Current workspace shows as selected with checkmark indicator
- Clicking a workspace filters the page to show only task lists and tasks from that workspace
- Use Alpine.js for dropdown open/close state (x-data, x-show, @click.away)
- Store selected workspace in session or URL parameter for persistence
- Update page content dynamically when workspace changes (HTMX or page reload)
- Workspace dropdown styling: white background, rounded corners, shadow, border

**User Menu Dropdown**
- Position user menu at top right of navigation bar
- Display user avatar (if available) + user's full name or first name
- If user has no profile image, show initials in a colored circle (use first + last initial)
- Clicking user name/avatar opens dropdown menu
- Dropdown menu items (in order):
  1. Profile (link to profile page)
  2. Preferences (link to preferences page)
  3. Horizontal divider line
  4. Logout (link to logout)
- Use Alpine.js for dropdown open/close state
- Close dropdown when clicking outside (Alpine.js @click.away directive)
- User menu styling: white background, rounded corners, shadow, right-aligned
- Avatar/initials styling: circular, 32px diameter, colored background based on user ID hash

**Navigation Bar Consistency**
- Navigation bar must render on task creation form page (`/workspace/<id>/tasklist/<id>/tasks/create/`)
- Navigation bar must render on task list view page
- Navigation bar must render on task detail view page
- Navigation bar must render on dashboard page
- Use consistent header height (64px) and padding across all pages
- Mobile responsive: collapse to hamburger menu on screens < 640px (future iteration)

## Visual Design

No visual assets provided. UI will follow existing patterns from accounts app with these specifications:

**Form Layout**
- Title field prominent at top with large text input, full width
- Description textarea below title, min-height 100px, auto-expand
- Due date and time fields side-by-side on same row for desktop, stacked on mobile
- Priority selector as horizontal button group with color badges
- Save and Cancel buttons in footer, right-aligned, with primary button styling on Save

**Modal Overlay (Task Editing)**
- Semi-transparent backdrop (bg-gray-900 bg-opacity-50) covering viewport
- White modal card centered on screen, max-width-2xl, rounded corners, shadow-xl
- Modal header with task title and close button (X icon)
- Form content in modal body with consistent padding
- Sticky footer with action buttons
- Close modal on backdrop click or Escape key (Alpine.js)

**Responsive Behavior**
- Mobile-first design with stacked layout for small screens
- Touch-friendly form controls with 44px minimum height
- Modal takes full screen on mobile with slide-up animation
- Priority buttons stack vertically on screens smaller than 640px

## Existing Code to Leverage

**Workspace Model (accounts/models.py)**
- Use existing Workspace model with owner and name fields
- Workspace.objects.filter(owner=request.user) to get user's workspaces
- Tasks have ForeignKey to Workspace with CASCADE delete
- Follow unique constraint pattern: workspace name unique per owner

**UserProfile & UserPreference Models**
- Use UserPreference.timezone for displaying due dates in user's timezone
- Use UserPreference.date_format for formatting date display
- Access via request.user.preferences.timezone and request.user.preferences.date_format

**Form Patterns (accounts/forms.py)**
- Follow RegistrationForm and ProfileUpdateForm patterns with Tailwind widget attributes
- Use consistent CSS classes: w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500
- Implement clean() method for cross-field validation
- Implement clean_<fieldname>() for field-specific validation
- Use help_text and error_messages attributes for user guidance

**Template Patterns (accounts/profile_update.html)**
- Follow template structure with header, main content area, form card
- Use Django template tags for CSRF, form field rendering, and error display
- Use Alpine.js for client-side interactivity (x-data, x-show, x-model)
- Load Alpine.js and Tailwind CSS from CDN in template head
- Display field errors below each field with red text styling

**Middleware & Authentication**
- Use TimezoneMiddleware to activate user's timezone for each request
- Use LoginRequiredMixin on all task views to enforce authentication
- Create WorkspaceAccessMixin to verify user owns workspace before allowing task operations

## Out of Scope
- Task deletion functionality (deferred to later iteration)
- TaskList deletion functionality (deferred to later iteration)
- Bulk task operations (deferred to later iteration)
- Task tags or labels (deferred to later iteration)
- Task assignment to other users (deferred to collaboration features)
- Task position/ordering within task list (deferred to later iteration)
- TaskList position/ordering within workspace (deferred to later iteration)
- Rich text editor for description (markdown only in this iteration)
- Task templates or duplication (deferred to later iteration)
- Recurring tasks (deferred to later iteration)
- TaskList templates or duplication (deferred to later iteration)
- Drag-and-drop task reordering (deferred to later iteration)
- Workspace creation by users (auto-created on signup, manual creation deferred)
- Workspace deletion by users (deferred to workspace management phase)
