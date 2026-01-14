# Task Breakdown: Core Task CRUD & Organization

## Overview

**Feature:** Task Creation and Task Editing
**Total Tasks:** 4 task groups with 26 sub-tasks
**Database Status:** Task model and tables already created and verified
**Focus:** Forms, views, templates, URL routing, and tests

## Task List

### Foundation Layer

#### Task Group 1: Django Forms & Validation
**Dependencies:** None (Task model already exists)

- [x] 1.0 Complete Django forms layer
  - [x] 1.1 Write 2-8 focused tests for TaskForm validation
    - Test title required validation
    - Test priority required validation
    - Test due_time requires due_date validation
    - Test cross-field validation in clean() method
    - Limit to maximum 8 tests covering critical validation paths only
  - [x] 1.2 Create TaskForm (ModelForm)
    - Base on Task model with fields: title, description, due_date, due_time, priority, status
    - Follow pattern from ProfileUpdateForm in accounts/forms.py
    - Apply Tailwind CSS widget attributes for consistent styling
    - Use TextInput for title with autofocus attribute
    - Use Textarea for description with markdown help text
    - Use DateInput with type='date' for due_date
    - Use TimeInput with type='time' for due_time
    - Use RadioSelect or Select for priority with P1/P2/P3/P4 choices
    - Use CheckboxInput for status toggle (active/completed)
  - [x] 1.3 Implement field-level validation
    - clean_title() - strip whitespace, ensure not empty
    - clean_description() - optional, max 10,000 chars
    - Add CSS classes: w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500
  - [x] 1.4 Implement form-wide validation (clean method)
    - Validate due_time requires due_date
    - Validate priority is one of P1/P2/P3/P4
    - Return ValidationError with field-specific error messages
  - [x] 1.5 Add form help text and labels
    - Title: "What needs to be done?" (max 255 characters)
    - Description: "Add details (supports markdown)"
    - Due Date: "When is this due?"
    - Due Time: "Specific deadline time (optional)"
    - Priority: "How urgent is this task?"
  - [x] 1.6 Run form validation tests
    - Run ONLY the 2-8 tests written in 1.1
    - Verify all validation rules work correctly
    - Do NOT run entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1 pass
- TaskForm validates all required fields
- Cross-field validation works (due_time requires due_date)
- Form widgets use consistent Tailwind CSS styling
- Help text provides clear guidance to users

### View Layer

#### Task Group 2: Django Class-Based Views & Mixins
**Dependencies:** Task Group 1 (Forms must exist)

- [x] 2.0 Complete view layer
  - [x] 2.1 Write 2-8 focused tests for task views
    - Test TaskCreateView requires authentication (LoginRequiredMixin)
    - Test TaskCreateView requires workspace access
    - Test TaskCreateView saves with correct workspace and created_by
    - Test TaskUpdateView requires authentication
    - Test TaskUpdateView verifies task ownership via workspace
    - Test HTMX request returns partial template (not full page)
    - Limit to maximum 8 tests covering critical view behaviors only
  - [x] 2.2 Create WorkspaceAccessMixin
    - Verify user owns workspace from URL parameter
    - Use get_object_or_404 for workspace lookup
    - Raise PermissionDenied if user is not workspace owner
    - Follow pattern from admin_required decorator in accounts/decorators.py
  - [x] 2.3 Create TaskCreateView (CreateView)
    - Inherit from LoginRequiredMixin, WorkspaceAccessMixin, CreateView
    - Use TaskForm from task group 1
    - Template: tasks/task_form.html
    - URL pattern: /workspace/<int:workspace_id>/tasks/create/
    - Override get_form_kwargs() to exclude workspace and created_by from form
    - Override form_valid() to set workspace and created_by from request
    - Success message: "Task created successfully!"
    - Redirect to same URL (form_valid returns redirect to self.request.path)
    - Use select_related('workspace', 'created_by') for queries
  - [x] 2.4 Create TaskUpdateView (UpdateView)
    - Inherit from LoginRequiredMixin, UpdateView
    - Use TaskForm from task group 1
    - Template: tasks/task_edit_form.html (partial for HTMX)
    - URL pattern: /tasks/<int:pk>/edit/
    - Override get_queryset() to verify user owns workspace containing task
    - Check request.htmx and return partial template if HTMX request
    - Success message: "Task updated successfully!"
    - For HTMX requests: return updated task HTML with HX-Trigger header
    - For regular requests: redirect to task list (future implementation)
    - Use select_related('workspace', 'created_by') for queries
  - [x] 2.5 Override get_context_data() for both views
    - Add workspace object to context for TaskCreateView
    - Add task object to context for TaskUpdateView
    - Add form_action URL for proper form submission
    - Add cancel_url for cancel button
  - [x] 2.6 Run view layer tests
    - Run ONLY the 2-8 tests written in 2.1
    - Verify authentication and permission checks work
    - Verify HTMX partial template rendering works
    - Do NOT run entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- Both views require authentication (LoginRequiredMixin)
- TaskCreateView enforces workspace access permissions
- TaskUpdateView verifies task ownership via workspace
- HTMX requests return partial templates
- Success messages display correctly
- Forms save with correct workspace and created_by values

### Frontend Layer

#### Task Group 3: Templates, HTMX & Alpine.js
**Dependencies:** Task Group 2 (Views must exist)

- [x] 3.0 Complete frontend templates and interactivity
  - [x] 3.1 Write 2-8 focused tests for template rendering
    - Test task_form.html renders all form fields correctly
    - Test autofocus on title field
    - Test priority selection displays with color indicators
    - Test due_time field conditional display (Alpine.js x-show)
    - Test modal overlay displays for task editing
    - Test form submission via HTMX
    - Limit to maximum 8 tests covering critical UI behaviors only
  - [x] 3.2 Create base task template structure
    - Create tasks/base_task.html extending base.html
    - Define task content blocks (header, form, footer)
    - Include Alpine.js and HTMX from CDN
    - Include Tailwind CSS from django-tailwind
    - Set up CSRF token for HTMX requests
  - [x] 3.3 Create task_form.html (Task Creation)
    - Full page layout with header "Create New Task"
    - Form card with white background, rounded corners, shadow
    - Title field: large text input, autofocus, full width
    - Description field: textarea, min-height 100px, markdown help text below
    - Due date and time: side-by-side on desktop (grid-cols-2), stacked on mobile
    - Priority selector: horizontal button group with color badges (P1=red-600, P2=orange-600, P3=yellow-600, P4=blue-600)
    - Priority buttons stack vertically on screens <640px (sm: breakpoint)
    - Save button: primary blue styling, right-aligned
    - Cancel button: secondary gray styling, left-aligned
    - Display Django messages for success/error feedback
    - Use {{ form.as_p }} or custom field rendering with Tailwind classes
  - [x] 3.4 Create task_edit_form.html (Task Editing - HTMX Partial)
    - Partial template for HTMX modal injection
    - Modal overlay: semi-transparent backdrop (bg-gray-900 bg-opacity-50)
    - Modal card: centered, max-w-2xl, white, rounded-lg, shadow-xl
    - Modal header: task title, close button (X icon)
    - Reuse form fields from task_form.html (consider creating form_fields.html include)
    - Add status toggle: checkbox for "Mark as complete"
    - Sticky footer with Save and Cancel buttons
    - Alpine.js modal controls: x-data="{ open: true }", x-show="open", @click.away="open=false"
    - Close on Escape key: @keydown.escape.window="open=false"
    - Mobile: full-screen modal with slide-up animation
  - [x] 3.5 Create _task_form_fields.html include (DRY)
    - Extract common form fields to reusable include
    - Title, description, due_date, due_time, priority fields
    - Include in both task_form.html and task_edit_form.html
    - Consistent field styling and error display
  - [x] 3.6 Implement Alpine.js interactivity
    - Due time field conditional display: x-show="$refs.due_date.value"
    - Priority button selection: track selected priority in Alpine data
    - Modal open/close state management
    - Form reset after successful creation (Alpine.js watches success message)
  - [x] 3.7 Implement HTMX behaviors
    - Form submission: hx-post="{{ form_action }}", hx-target="#modal", hx-swap="innerHTML"
    - Edit link trigger: hx-get="/tasks/{{ task.id }}/edit/", hx-target="#modal"
    - Success response: HX-Trigger header to close modal and refresh task display
    - Error response: swap form with errors inline
    - Loading states: hx-indicator for submit button
  - [x] 3.8 Apply responsive design
    - Mobile-first layout with stacked fields
    - Touch-friendly controls (44px minimum height for buttons)
    - Modal full-screen on mobile (<640px)
    - Priority buttons vertical stack on mobile
    - Due date/time fields stack on mobile, side-by-side on desktop (sm:grid-cols-2)
  - [x] 3.9 Add priority visual indicators
    - P1: red-600 background, white text, "Urgent" label
    - P2: orange-600 background, white text, "High" label
    - P3: yellow-600 background, gray-900 text, "Medium" label
    - P4: blue-600 background, white text, "Low" label
    - Priority badge on task display (if task list exists)
  - [x] 3.10 Run frontend template tests
    - Run ONLY the 2-8 tests written in 3.1
    - Verify all form fields render correctly
    - Verify Alpine.js conditional display works
    - Verify HTMX modal loading works
    - Do NOT run entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 3.1 pass
- Task creation form renders with all fields and proper styling
- Task editing modal loads via HTMX and displays correctly
- Priority selector displays with color-coded buttons
- Due time field shows/hides based on due date value (Alpine.js)
- Modal closes on backdrop click and Escape key
- Responsive design works on mobile, tablet, and desktop
- Form fields use consistent Tailwind CSS styling
- Success/error messages display clearly

### URL Routing & Integration

#### Task Group 4: URL Configuration & Full Integration Testing
**Dependencies:** Task Groups 1-3 (Forms, views, and templates must exist)

- [x] 4.0 Complete URL routing and integration testing
  - [x] 4.1 Review existing tests and identify gaps
    - Review the 2-8 tests from Task Group 1 (forms)
    - Review the 2-8 tests from Task Group 2 (views)
    - Review the 2-8 tests from Task Group 3 (templates)
    - Total existing tests: approximately 6-24 tests
    - Identify critical integration gaps (end-to-end workflows)
  - [x] 4.2 Create tasks/urls.py (ALREADY COMPLETE - VERIFIED)
    - URL pattern: path('workspace/<int:workspace_id>/tasks/create/', TaskCreateView.as_view(), name='task-create')
    - URL pattern: path('tasks/<int:pk>/edit/', TaskUpdateView.as_view(), name='task-edit')
    - Follow naming convention from accounts/urls.py
    - Use app_name = 'tasks' for namespacing
  - [x] 4.3 Include tasks URLs in project urlpatterns (ALREADY COMPLETE - VERIFIED)
    - Add path('', include('tasks.urls')) to workstate/urls.py
    - Verify URL namespacing works: reverse('tasks:task-create', kwargs={'workspace_id': 1})
  - [x] 4.4 Create modal container in base template (ALREADY COMPLETE - VERIFIED)
    - Add <div id="modal"></div> to base.html for HTMX injection
    - Ensure modal container is outside main content area
    - Add z-index: 50 for proper overlay stacking
  - [x] 4.5 Write up to 10 additional integration tests maximum
    - End-to-end task creation workflow (visit form → submit → verify success)
    - End-to-end task editing workflow (click edit → modal loads → submit → verify update)
    - Workspace permission enforcement (cannot create task in another user's workspace)
    - HTMX modal interaction (load form → close on backdrop click)
    - Form persistence after creation (fields reset, success message shown)
    - Focus ONLY on critical user workflows for this feature
    - Do NOT test edge cases, accessibility, or performance
    - Limit to maximum 10 new integration tests
  - [x] 4.6 Run feature-specific tests only
    - Run tests from Task Groups 1-3 (approximately 6-24 tests)
    - Run new integration tests from 4.5 (maximum 10 tests)
    - Expected total: approximately 16-34 tests maximum
    - Verify all critical task creation and editing workflows pass
    - Do NOT run entire application test suite
  - [x] 4.7 Manual verification checklist
    - Create workspace if none exists
    - Visit /workspace/1/tasks/create/ and verify form loads
    - Submit valid task and verify success message
    - Verify form resets after creation
    - Create a second task quickly to test workflow
    - Click edit on a task and verify modal loads via HTMX
    - Update task in modal and verify changes save
    - Test mobile responsive design (resize browser)
    - Test priority color indicators display correctly
    - Test due time field shows/hides based on due date

**Acceptance Criteria:**
- All feature-specific tests pass (approximately 16-34 tests total)
- URL routing works correctly with proper namespacing
- Task creation form accessible at /workspace/<id>/tasks/create/
- Task editing modal loads via HTMX at /tasks/<id>/edit/
- End-to-end workflows function correctly (create and edit tasks)
- Workspace permissions enforced (users can only create tasks in their workspaces)
- HTMX modal interactions work smoothly
- Form resets after successful creation
- Maximum 10 additional integration tests added
- Manual verification checklist confirms all functionality works

## Execution Order

Recommended implementation sequence:
1. **Foundation Layer** (Task Group 1) - Django forms and validation
2. **View Layer** (Task Group 2) - Class-based views and mixins
3. **Frontend Layer** (Task Group 3) - Templates, HTMX, Alpine.js
4. **URL Routing & Integration** (Task Group 4) - URL config and end-to-end testing

## Testing Philosophy

This feature follows a **focused testing approach**:
- Each task group (1-3) writes 2-8 focused tests covering ONLY critical behaviors
- Task group 4 adds maximum 10 integration tests to fill gaps
- **Total expected tests: 16-34 tests maximum**
- Focus on critical user workflows, NOT comprehensive coverage
- Edge cases, performance, and accessibility testing are deferred

## Notes

### Database Layer
- Task model and migrations are **already complete** - do not recreate
- TaskManager with query methods already exists
- Model validation methods already implemented

### Technology Stack Alignment
- **Django 5.x** with class-based views (CreateView, UpdateView)
- **HTMX 1.9+** for dynamic modal loading and form submission
- **Alpine.js 3.x** for client-side interactivity (modal controls, conditional display)
- **Tailwind CSS 3.x** via django-tailwind for styling
- **pytest** for testing

### Code Reuse Patterns
- Follow **ProfileUpdateForm** pattern from accounts/forms.py for form styling
- Follow **LoginRequiredMixin** pattern from accounts/views.py for authentication
- Follow **admin_required** pattern from accounts/decorators.py for WorkspaceAccessMixin
- Follow template structure from accounts app for consistency

### Out of Scope (Deferred)
- Task deletion functionality
- Task listing and filtering views
- Bulk task operations
- Task sections or grouping
- Task tags or labels
- Task assignment to other users
- Task position/ordering
- Rich text editor for description (markdown only)
- Task templates or duplication
- Recurring tasks

### Future Integration Points
- Project assignment (field exists but nullable, not used yet)
- Task list view (will consume task creation and editing functionality)
- Task detail view (will display markdown-rendered description)
- Collaboration features (will add task assignment)
