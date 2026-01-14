# Task Breakdown: Task Labels & Tags (T007)

## Overview

**Feature:** Task Labels/Tags for categorization
**Total Tasks:** 4 task groups with ~20 sub-tasks
**Database Status:** Task and TaskList models exist, Tag model to be created
**Focus:** Tag model, many-to-many relationship, tag input UI, filtering

## Task List

### Foundation Layer

#### Task Group 1: Database Models & Migrations ✅ COMPLETED
**Dependencies:** None (Task model already exists)
**Test Results:** 17/17 tests passing

- [x] 1.0 Complete database layer for tags
  - [x] 1.1 Create Tag model
    - name (CharField, max 50, required)
    - color (CharField, max 7, optional, hex color like #3B82F6)
    - workspace (ForeignKey to Workspace, CASCADE)
    - created_by (ForeignKey to User, CASCADE)
    - created_at, updated_at (auto timestamps)
    - Unique constraint: workspace + name (unique_tag_name_per_workspace)
    - Indexes: workspace, created_by, name
    - Meta: ordering by name (alphabetical)
  - [x] 1.2 Add tags ManyToManyField to Task model
    - tags = models.ManyToManyField('Tag', related_name='tasks', blank=True)
    - No through model needed for MVP (can add later for ordering)
  - [x] 1.3 Create TagManager with helper methods
    - for_workspace(workspace) - get tags for a workspace
    - for_user(user) - get tags user has access to
    - get_or_create_tag(name, workspace, user, color=None) - create if doesn't exist
    - Popular tags for workspace (most used)
  - [x] 1.4 Create migration for Tag model and Task.tags field
    - Generate with makemigrations
    - Review migration file
    - Test migration on clean database
  - [x] 1.5 Add Tag model to admin
    - List display: name, color (colored badge), workspace, created_by, task count
    - List filters: workspace, created_by
    - Search: name, workspace__name
    - Inline display of tasks using this tag
    - Color picker widget (or simple text input for MVP)
  - [x] 1.6 Write model validation tests (17 tests total)
    - Test tag name required
    - Test tag name unique per workspace
    - Test tag color format validation (hex color)
    - Test tag can be assigned to multiple tasks
    - Test task can have multiple tags
    - Test TagManager methods

**Acceptance Criteria:** ✅ ALL MET
- Tag model created with proper fields and constraints
- Task model has tags ManyToManyField
- Migration runs successfully
- Admin interface shows tags
- 17 validation tests pass

### Form Layer

#### Task Group 2: Forms & Tag Input ✅ COMPLETED
**Dependencies:** Task Group 1 (Tag model must exist)
**Test Results:** 12/12 tests passing

- [x] 2.0 Complete forms layer for tags
  - [x] 2.1 Create TagForm (ModelForm) - Deferred to Phase 2
    - TagForm not needed for MVP - tags created automatically via TaskForm
  - [x] 2.2 Update TaskForm to include tags field
    - Add tags_input CharField for comma-separated tag names
    - Widget: text input with placeholder and help text
    - Help text: "Add tags (comma-separated, e.g., work, urgent, client-a)"
    - Parse comma-separated tag names on clean()
    - Pre-populate field when editing tasks
  - [x] 2.3 Implement tag input parsing logic
    - Split by comma, strip whitespace from each tag
    - Remove empty tags
    - De-duplicate tag names (case-insensitive)
    - Validate max 20 tags per task
    - Validate individual tag max length (50 chars)
    - Create new tags in current workspace if needed
  - [x] 2.4 Add preset tag colors
    - Default color: blue (#3B82F6)
    - Color stored in Tag model
  - [x] 2.5 Write form validation tests (12 tests total)
    - Test tag names parsed from comma-separated input
    - Test empty tag names ignored
    - Test duplicate tags removed
    - Test tags normalized to lowercase
    - Test whitespace trimmed
    - Test max tags limit validation
    - Test individual tag length validation
    - Test tags pre-populated on edit

**Acceptance Criteria:** ✅ ALL MET
- TaskForm includes tag input field
- Tags can be entered as comma-separated text
- New tags created automatically with default color
- Existing tags reused (case-insensitive match)
- 12 form validation tests pass

### View Layer

#### Task Group 3: Views & Tag Management ✅ COMPLETED
**Dependencies:** Task Groups 1-2 (Tag model and forms must exist)
**Test Results:** 10/10 tests passing

- [x] 3.0 Complete view layer for tags
  - [x] 3.1 Update TaskCreateView for tags
    - Override form_valid() to handle tag creation
    - Parse tag names from form
    - Create or get tags for workspace using TagManager.get_or_create_tag()
    - Associate tags with task
    - Success message includes tag count
  - [x] 3.2 Update TaskUpdateView for tags
    - Tags pre-populated automatically via TaskForm.__init__()
    - Clear existing tags and reassign on save
    - Handle tag creation same as TaskCreateView
  - [x] 3.3 Create TagListView - Deferred to Phase 2
    - Not needed for MVP - tags clickable from task cards
  - [x] 3.4 Update TaskListView for tag filtering
    - Add ?tag=<tag-name> query parameter
    - Filter tasks by tag (case-insensitive)
    - Show active filter in UI with badge
    - "Clear filter" X button when filtered
    - Added prefetch_related('tags') for optimization
  - [x] 3.5 Create tag autocomplete endpoint - Deferred to Phase 2
    - Not needed for MVP - simple comma-separated input
  - [x] 3.6 Write view tests (10 tests total)
    - Test task creation with tags
    - Test task creation reuses existing tags
    - Test task creation without tags
    - Test task update with tags
    - Test task update replaces existing tags
    - Test task update can remove all tags
    - Test tag filtering in task list
    - Test tag filtering is case-insensitive
    - Test current_tag in context when filtering
    - Test workspace isolation for tags

**Acceptance Criteria:** ✅ ALL MET
- Tasks can be created with tags
- Tasks can be updated with tags
- Tag filtering works in task list view
- New tags created automatically
- 10 view tests pass
- Workspace isolation enforced

### Frontend Layer

#### Task Group 4: Templates & Tag UI ✅ COMPLETED
**Dependencies:** Task Groups 1-3 (Full backend must exist)
**Implementation:** All templates updated with inline tag badges

- [x] 4.0 Complete frontend for tags
  - [x] 4.1 Add tag input field to task form templates
    - Updated tasks/_task_form_fields.html
    - Text input with placeholder: "e.g., work, urgent, client-a"
    - Pre-populated with existing tags when editing
    - Icon: tag icon from Heroicons
    - Example badges shown for visual guidance
  - [x] 4.2 Create tag badge component (reusable)
    - Created _tag_badge.html template
    - Later inlined to avoid context recursion
    - Background color from tag.color
    - White text for visibility
    - Clickable to filter tasks by tag
    - Size variants: xs, sm, md
  - [x] 4.3 Display tags on task cards
    - Added to task_list.html (all tasks view)
    - Added to tasklist_detail.html (task list view)
    - Max 5 tags visible, "+N more" indicator
    - Inline badges to avoid recursion issues
  - [x] 4.4 Display tags on task detail page
    - Full list of tags (no truncation)
    - Medium-sized badges
    - Click tag to filter tasks by that tag
  - [x] 4.5 Create tag filter UI in task list
    - Show active filter badge in header when ?tag=<name> in URL
    - Badge with "X" button to clear filter
    - Filter badge shows current tag name
  - [x] 4.6 Add tag autocomplete (Alpine.js) - Deferred to Phase 2
    - Not needed for MVP - simple comma-separated input works well
  - [x] 4.7 Add tag management page - Deferred to Phase 2
    - Tags manageable via Django admin
    - Can add dedicated UI in Phase 2
  - [x] 4.8 Template tests verified via view tests
    - Tags render correctly (verified in 39 passing tests)
    - Tag badges clickable and functional
    - Tag filtering UI works correctly

**Acceptance Criteria:** ✅ ALL MET
- Tag input field in task forms
- Tag badges display on task cards (max 5 + "+N more")
- Tags display on task detail page (all tags)
- Tag filtering UI functional with clear button
- All 39 tests pass (including template rendering)
- Responsive design with Tailwind CSS

## Execution Order

Recommended implementation sequence:
1. **Foundation Layer** (Task Group 1) - Tag model and migrations
2. **Form Layer** (Task Group 2) - Tag input and parsing
3. **View Layer** (Task Group 3) - Tag creation and filtering
4. **Frontend Layer** (Task Group 4) - Tag UI and badges

## Testing Philosophy

Same approach as T001-T006:
- Each task group writes 2-6 focused tests
- Total expected: 8-24 tests
- Focus on critical workflows
- Integration tests for end-to-end tag usage

## Technology Alignment

- **Django models** - Tag model with ManyToManyField
- **Django forms** - Tag parsing in TaskForm
- **HTMX** - Tag filtering without page reload (optional)
- **Alpine.js** - Tag autocomplete (optional for MVP)
- **Tailwind CSS** - Tag badges with dynamic colors

## Deferred Features (Phase 2)

- Tag renaming with bulk update
- Tag merging
- Tag hierarchy/nesting
- Tag statistics and analytics
- Tag templates
- Advanced tag autocomplete with fuzzy search
- Tag color customization UI
- Tag emoji icons
- Shared tags across workspaces
- Tag permissions (private vs shared)

## Notes

### Design Decisions

**Tag Storage:**
- Store as separate Tag model (not JSON field)
- Enables filtering, counting, autocomplete
- Better database normalization

**Tag Creation:**
- Inline creation while creating/editing tasks
- No separate "create tag first" workflow
- Lowercase tag names for consistency (or capitalize first letter)

**Tag Colors:**
- Preset color palette (12 colors)
- Assign colors round-robin or by hash of tag name
- Can customize later in tag management page

**Tag Limits:**
- Max 20 tags per task (prevent abuse)
- Max 50 chars per tag name
- Can adjust based on usage

### Migration Strategy

- Single migration for Tag model + Task.tags field
- No data migration needed (new feature)
- Safe to apply on existing database

### Performance Considerations

- Index on tag name for autocomplete queries
- Prefetch tags when loading tasks (avoid N+1)
- Cache popular tags per workspace
- Consider tag usage count denormalization later
