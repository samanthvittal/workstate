# Specification: Task Search (T009)

## Goal
Provide comprehensive full-text search functionality across tasks using PostgreSQL's tsvector/tsquery capabilities, enabling users to quickly find tasks by searching titles, descriptions, subtasks, and comments with live results dropdown in the navigation bar and a dedicated search results page with advanced filtering and sorting options.

## User Stories
- As a user, I want to search across all my accessible tasks by typing keywords in the navigation bar, so that I can quickly find specific tasks without navigating through multiple pages
- As a user, I want to see live search results as I type with highlighted matches, so that I can immediately identify relevant tasks and navigate to full results if needed

## Specific Requirements

**PostgreSQL Full-Text Search Implementation**
- Add `search_vector` column (tsvector type) to tasks table with GIN index for performance
- Create database trigger to automatically update search_vector when task title or description changes
- Configure weighted search ranking: title (weight A), description (weight B), subtask titles (weight C), comments (weight D)
- Use `ts_rank_cd` function for relevance scoring in search queries
- Implement `to_tsvector('english', ...)` for text indexing and `to_tsquery('english', ...)` for query parsing
- Support advanced operators: AND (&), OR (|), NOT (!), phrase search ("exact match")
- Sanitize search input to prevent tsvector injection attacks
- Create separate search_vector columns for related models (subtasks, comments) with their own GIN indexes

**Search History and Saved Searches Models**
- Create SearchHistory model with fields: user (FK to User), query (CharField 255), searched_at (DateTimeField), result_count (IntegerField)
- Create SavedSearch model with fields: user (FK to User), name (CharField 100), query (TextField), filters (JSONField for storing filter state), created_at, updated_at
- Add database indexes on user and searched_at for SearchHistory model
- Add unique constraint on SavedSearch for user + name combination
- Limit SearchHistory to most recent 50 searches per user (implement cleanup logic)
- Store filter state in SavedSearch including: workspace_id, tag_names, status, priority, date_range

**Navigation Bar Search Component**
- Add search input field to nav.html template positioned centrally between logo and user menu
- Implement HTMX-powered live search with debouncing (300ms delay) using hx-get and hx-trigger="keyup changed delay:300ms"
- Create SearchDropdownView that returns partial template with preview results (max 5 tasks)
- Display dropdown results with: task title (highlighted), workspace name, priority badge, due date indicator
- Include "View all results" link at dropdown bottom when results exist
- Show "No results found" message when query returns empty
- Hide dropdown when input is cleared or loses focus (Alpine.js @click.away)
- Ensure dropdown z-index is higher than all other UI elements for proper visibility

**Search Results Page**
- Create dedicated search results page at /search/ URL endpoint
- Accept query parameter 'q' for search term from navigation bar or direct access
- Display search query prominently at top of page with result count
- Show results in paginated list using existing _task_card.html partial for consistency
- Implement pagination with 25 results per page
- Display "Recent Searches" sidebar section with links to previous 10 queries
- Display "Saved Searches" sidebar section with saved query shortcuts
- Include empty state message when no results found with suggestions to refine search

**Search Result Display and Highlighting**
- Generate text snippets (150 characters) around matched terms using ts_headline function
- Highlight search terms in snippets using <mark> tag with yellow background styling
- Display full task title with highlighting if title matches search query
- Show workspace name badge for each result to indicate task location
- Include standard task metadata: priority badge, due date label, tags, task list name
- Use identical card styling as existing task list views for UI consistency

**Sorting Options for Search Results**
- Default sort by relevance (ts_rank_cd score descending)
- Add sort dropdown with options: Relevance (default), Due Date (earliest first), Priority (P1→P4), Created Date (newest first)
- Preserve search query and filters when changing sort order
- Update URL with sort parameter for bookmarkable sorted results
- Highlight active sort option in dropdown using Tailwind bg-gray-100 styling

**Filtering Options for Search Results**
- Add filters sidebar matching existing task_sidebar.html pattern for consistency
- Workspace filter: dropdown showing all accessible workspaces with task counts
- Tag filter: tag cloud or dropdown showing tags used in search results with counts
- Status filter: radio buttons for Active, Completed, All (default: Active)
- Priority filter: checkboxes for P1, P2, P3, P4 allowing multiple selections
- Apply filters using Django QuerySet filter() chaining for efficient queries
- Show active filters as removable badges above results (matching task_list.html pattern)
- Clear individual filters or all filters with single click

**Advanced Search Features**
- Support AND operator using '&' or 'AND' keyword between terms
- Support OR operator using '|' or 'OR' keyword between terms
- Support NOT operator using '!' prefix or 'NOT' keyword before term
- Support phrase search using double quotes "exact phrase match"
- Support regex patterns using REGEX: prefix with PostgreSQL regex matching
- Validate regex patterns to prevent ReDoS attacks (limit complexity, timeout)
- Show syntax help tooltip on search page explaining operator usage
- Display error message for invalid search syntax with correction suggestions

**Saved Search Functionality**
- Add "Save Search" button on search results page when query is active
- Show modal dialog prompting for search name when saving
- Store current query, active filters, and sort order in SavedSearch model
- Display saved searches in sidebar with edit and delete actions
- Allow users to rename or delete saved searches inline
- Clicking saved search loads query, filters, and sort order instantly
- Limit to 20 saved searches per user with validation

**Recent Search History**
- Automatically record every search query in SearchHistory model on search execution
- Store query text, result count, and timestamp for each search
- Display recent searches in sidebar as clickable links (most recent 10)
- Do not store searches with empty queries or searches with 0 results
- Allow users to clear entire search history with confirmation dialog
- Auto-prune history beyond 50 entries per user using post_save signal or periodic task

**Permission and Access Control**
- Restrict search results to tasks in workspaces owned by authenticated user
- Use task_list__workspace__owner filter in all search queries
- Verify user authentication before allowing search access (LoginRequiredMixin)
- Ensure saved searches and history are user-scoped and never leak across users
- Validate workspace_id filter matches user's accessible workspaces before applying

## Visual Design

No visual mockups provided. Maintain consistency with existing Workstate UI patterns:

**Navigation Bar Search Input**
- Position search input centrally in nav.html between logo and user menu
- Use Tailwind styling matching existing form inputs: border-gray-300, focus:ring-blue-500, rounded-md
- Include search icon (magnifying glass SVG) inside input on left side
- Set placeholder text: "Search tasks..."
- Make input responsive: full width on mobile, max-w-md on desktop
- Style dropdown with white background, shadow-lg, rounded-md, border matching existing dropdowns

**Search Results Page Layout**
- Use existing task_list.html as layout template for consistency
- Include standard nav.html at top and task_sidebar.html on left side
- Position search-specific filters in right sidebar or above results area
- Display sort dropdown in header area next to result count
- Maintain spacing and typography consistent with existing task list pages
- Use existing _task_card.html partial for individual result display

**Highlighting and Visual Feedback**
- Style <mark> tags with bg-yellow-200 text-gray-900 for highlighted search terms
- Use existing priority badge colors (P1: red, P2: orange, P3: yellow, P4: blue)
- Display workspace name badge with bg-gray-100 text-gray-700 styling
- Show active filters as removable badges with bg-blue-50 border-blue-200 matching task_list.html
- Use standard Tailwind hover states (hover:bg-gray-50) for interactive elements

**Saved Searches and History Sidebar**
- Group saved searches in collapsible section with header "Saved Searches"
- Group recent searches in collapsible section with header "Recent Searches"
- Use list styling matching existing sidebar navigation items
- Include edit/delete icons for saved searches using existing SVG icon set
- Style active/hover states consistently with existing sidebar items

## Existing Code to Leverage

**Task Model and Manager (tasks/models.py)**
- Extend TaskManager with search-specific query methods (search_tasks, filter_by_query)
- Use existing custom manager patterns (for_workspace, for_user) for permission filtering
- Follow existing index patterns for adding search_vector GIN index
- Replicate clean() and validation patterns for new SearchHistory and SavedSearch models
- Use existing timestamp fields pattern (created_at, updated_at) for new models

**Task Views and Mixins (tasks/views.py)**
- Replicate LoginRequiredMixin and WorkspaceAccessMixin patterns for search views
- Follow TaskListView pagination pattern (paginate_by = 50) for search results
- Use existing select_related and prefetch_related optimization patterns to avoid N+1 queries
- Mirror get_context_data pattern for adding filters, counts, and metadata to search context
- Follow HTMX response patterns from TaskToggleStatusView for live search dropdown

**Task List Template (templates/tasks/task_list.html)**
- Replicate filter display logic for showing active filters as removable badges
- Use identical empty state styling and messaging for "no results" state
- Follow pagination HTML structure for search results pagination
- Maintain Alpine.js keyboard shortcut patterns if applicable to search results
- Reuse task count and status filter UI patterns in search results header

**Task Card Partial (templates/tasks/_task_card.html)**
- Reuse entire _task_card.html partial for displaying individual search results
- No modifications needed - existing card shows all required metadata
- Ensure workspace name is displayed in card metadata (add if not present)
- Maintain HTMX interactions for toggle status and archive actions
- Follow existing hover and focus state styling patterns

**Navigation Bar (templates/includes/nav.html)**
- Insert search input between logo div and user menu div in existing flex layout
- Use existing Alpine.js data attribute pattern for dropdown state management
- Follow existing dropdown styling from user menu dropdown for search results dropdown
- Maintain responsive behavior patterns (hidden on mobile, visible on desktop)
- Replicate @click.away pattern for closing search dropdown when clicking outside

## Out of Scope

The following features are explicitly OUT OF SCOPE for this specification and MUST NOT be implemented:

- Elasticsearch or other external search service integration
- Search analytics or usage tracking beyond basic history
- Machine learning-based search result ranking or personalization
- Voice search or speech-to-text input
- Image or file content search within task attachments
- Cross-workspace search for team members or collaborators (only owner access)
- Search API endpoints for external integrations or mobile apps
- Fuzzy matching or typo correction for search queries
- Search result caching beyond standard database query caching
- Autocomplete or search suggestions based on previous queries
