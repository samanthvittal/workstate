# Requirements: Core Task Creation & Editing

## Scope

**Focus:** Task Creation and Task Editing only (MVP iteration)
**Deferred:** Task deletion, listing, filtering, bulk operations, organization features

## User Stories

### Task Creation
- As a user, I want to create a new task with a title and optional details
- As a user, I want to set a due date and priority when creating a task
- As a user, I want tasks to be automatically associated with my workspace

### Task Editing
- As a user, I want to edit any field of an existing task
- As a user, I want to mark a task as complete/incomplete
- As a user, I want my changes saved immediately with clear feedback

## Task Model (Django Best Practices)

### Core Fields
- `title` (CharField, max_length=255, required)
- `description` (TextField, optional, supports markdown)
- `due_date` (DateField, nullable)
- `due_time` (TimeField, nullable)
- `priority` (CharField, choices: P1/P2/P3/P4/None)
- `status` (CharField, choices: active/completed, default=active)
- `workspace` (ForeignKey to Workspace, required)
- `project` (ForeignKey to Project, nullable) - for future use
- `created_by` (ForeignKey to User, required)
- `created_at` (DateTimeField, auto_now_add)
- `updated_at` (DateTimeField, auto_now)

### Model Design Patterns
- Use Django's model manager for common queries
- Implement model methods for business logic (e.g., `mark_complete()`, `is_overdue()`)
- Add database indexes on: workspace, created_by, due_date, status
- Use appropriate database constraints (e.g., CHECK constraints for valid priorities)
- Implement `__str__()` for admin interface

## Views & Forms (Django Best Practices)

### Task Creation
- **Pattern:** Class-based view (CreateView)
- **Form:** Django ModelForm with crispy-forms or custom rendering
- **URL:** `/tasks/create/` or `/workspace/<id>/tasks/create/`
- **Template:** Server-side rendered with HTMX for dynamic behavior
- **Validation:** Server-side validation (required), client-side for UX

### Task Editing
- **Pattern:** Class-based view (UpdateView)
- **Form:** Same ModelForm as creation (DRY principle)
- **URL:** `/tasks/<id>/edit/`
- **Template:** Can be modal overlay or dedicated page
- **HTMX:** Use for in-place editing without full page reload

### Success/Error Handling
- Django messages framework for user feedback
- Redirect to task list or detail view on success
- Display form errors inline with field-level validation messages

## UI/UX Approach

### Technology Stack (Per Project Standards)
- **Backend:** Django 5.x with class-based views
- **Templates:** Django templates with template inheritance
- **Interactivity:** HTMX for dynamic updates
- **Client-side:** Alpine.js for modals, date pickers
- **Styling:** Tailwind CSS utility classes
- **Icons:** Heroicons or Lucide

### Form Layout
- Clean, minimal design
- Title field prominent and autofocused
- Optional fields collapsible or below-the-fold
- Due date with calendar picker (Alpine.js)
- Priority as visual buttons or dropdown
- Clear "Save" and "Cancel" actions

### Responsive Design
- Mobile-first approach
- Touch-friendly form controls (44px minimum)
- Stack fields vertically on mobile
- Optimize for quick task entry

## Validation Rules

### Title
- Required field
- Max length: 255 characters
- No leading/trailing whitespace
- Minimum 1 non-whitespace character

### Description
- Optional
- Markdown support (stored as plain text, rendered as markdown)
- Max length: 10,000 characters (configurable)

### Due Date/Time
- Due date must be valid date format
- Due time requires due date to be set
- Allow past dates (for flexibility - user may want to log overdue tasks)
- Time is optional even if date is set

### Priority
- Optional field (can be None/null)
- Must be one of: P1, P2, P3, P4, or None
- Display as: P1 (Urgent, Red), P2 (High, Orange), P3 (Medium, Yellow), P4 (Low, Blue)

### Workspace
- Required (automatically set from current user context)
- User must have access to workspace
- Enforce at model and view level

## Integration Points

### Workspace System
- All tasks belong to a workspace
- Current workspace determined by:
  - User's last selected workspace (stored in session)
  - User's default workspace
  - First available workspace if none selected
- Workspace switching filters visible tasks

### User Association
- Tasks linked to creating user via `created_by`
- User must be member of workspace to create tasks
- Use Django's `request.user` in views

### Future Integration Points (Not in This Iteration)
- Project assignment (field exists but optional)
- Tags/labels (deferred to later iteration)
- Task sections (deferred to Project Management phase)

## Django Best Practices to Follow

### Models
- Use model managers for common queries (e.g., `Task.objects.active()`, `Task.objects.for_workspace(workspace)`)
- Implement model methods for business logic
- Use `select_related()` and `prefetch_related()` to avoid N+1 queries
- Add appropriate `Meta` class with ordering, indexes, constraints

### Views
- Use class-based views (CreateView, UpdateView) with mixins
- LoginRequiredMixin for authentication
- Custom mixins for workspace access control
- Override `form_valid()` for custom save logic
- Use `get_context_data()` for additional template context

### Forms
- Use ModelForm for DRY principle
- Custom widgets for better UX (date picker, priority selector)
- Field-level validation methods (`clean_<fieldname>()`)
- Form-wide validation in `clean()`
- Use `crispy-forms` or custom templates for rendering

### Templates
- Template inheritance (base.html → task_form.html)
- Include files for reusable components
- Use Django's form rendering with custom layouts
- HTMX attributes for dynamic behavior
- Alpine.js for client-side interactivity (modals, date pickers)

### URL Patterns
- RESTful URL design
- Named URL patterns for reverse lookups
- Namespace URLs by app (e.g., `tasks:create`)

### Security
- CSRF protection (Django default)
- User authentication required
- Permission checks (user must belong to workspace)
- SQL injection prevention (Django ORM)
- XSS prevention (Django template auto-escaping)

## Testing Requirements

### Model Tests
- Test task creation with valid data
- Test validation constraints (required fields, max lengths)
- Test model methods (e.g., `is_overdue()`, `mark_complete()`)
- Test database constraints
- Test foreign key relationships (workspace, user)

### View Tests
- Test authenticated access (redirect if not logged in)
- Test workspace permission checks
- Test form submission with valid data
- Test form validation errors
- Test redirect after successful save
- Test HTMX response vs. full page load

### Form Tests
- Test field validation (required, max length, format)
- Test custom validation logic
- Test form rendering with initial data
- Test error message display

## User Decisions

1. **Task Editing UI:** ✅ A) Modal overlay (HTMX swap) - keeps user in context
2. **After Save Behavior:** ✅ C) Stay on form and show success message (create another)
3. **Description Field:** ✅ A) Use a simple textarea, render markdown on display
4. **Priority Field:** ✅ A) Required field (every task must have a priority)

## Implementation Notes

- Task editing will use HTMX to load form in modal overlay
- After creation, form resets with success message for quick task entry
- Description stored as plain text, rendered as markdown in display views
- Priority is mandatory field with choices: P1, P2, P3, P4
