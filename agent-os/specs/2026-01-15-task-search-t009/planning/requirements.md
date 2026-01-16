# Spec Requirements: Task Search (T009)

## Initial Description
Full-text search across tasks with title and description search, workspace filtering, search results page with highlighting, recent searches, and navigation bar search input

## Requirements Discussion

### First Round Questions

**Q1: Search Technology - I assume we should use PostgreSQL's built-in full-text search capabilities (tsvector/tsquery) since we're using PostgreSQL as our primary database. Is that correct, or would you prefer a dedicated search service like Elasticsearch?**
**Answer:** PostgreSQL built-in full-text search (tsvector/tsquery)

**Q2: Navigation Bar Search UX - I'm thinking the navigation bar search should show live search results in a dropdown as the user types (with a "View all results" link to the full search page). Should we use this pattern, or would you prefer a simple input that navigates to the search results page on submit?**
**Answer:** Live search results dropdown as user types (show preview with "View all results" link)

**Q3: Search Scope - Fields - I assume we should search across: task titles, task descriptions, subtask titles, and task comments. Should we include all of these, or are some out of scope?**
**Answer:**
- Task title ✓
- Task description ✓
- Subtask titles ✓
- Task comments ✓

**Q4: Search Scope - Workspaces - Should the search be limited to the currently active workspace, or should it search across all workspaces the user has access to? If searching all workspaces, should we display the workspace name in the search results?**
**Answer:** Search all accessible workspaces. Search results should display the workspace name for each task.

**Q5: Search Result Highlighting - Should we show matched text snippets with highlighted search terms in the results, or just display the full task title/description?**
**Answer:** Show snippets (approximately 150 characters) with matched search terms highlighted

**Q6: Recent Searches Storage - Should recent searches be stored in browser localStorage (session-specific) or in the database (persistent across devices/sessions)?**
**Answer:** Persistent across sessions (store in database)

**Q7: Search Results Sorting & Filtering - I'm thinking we should support sorting by relevance (default), due date, and priority. Should we also allow filtering results by project, tags, or status (active/completed)?**
**Answer:**
- Sortable by: relevance (default), due date, priority, created date
- Filterable by: project, tags, status (active/completed), priority

**Q8: Out of Scope - Are there any search-related features we should explicitly exclude from this iteration? For example: saved search queries, advanced search operators (AND, OR, NOT), or regex support?**
**Answer:** None - all features are in scope including advanced search operators (AND, OR, NOT), regex support, and saved search queries

**Q9: Existing Code to Reference - Are there existing features in your codebase with similar patterns we should reference? For example: similar interface elements or UI components to re-use, comparable page layouts or navigation patterns, related backend logic or service objects, existing models or controllers with similar functionality?**
**Answer:** None specified - keep UI consistent with current implementation

**Q10: Visual Assets Request - Do you have any design mockups, wireframes, or screenshots that could help guide the development?**
**Answer:** No visual mockups provided - maintain consistency with existing UI patterns

### Existing Code to Reference

No similar existing features identified for reference.

User requested to keep UI consistent with current implementation patterns.

### Follow-up Questions

No follow-up questions were necessary. All requirements were clearly specified in the initial answers.

## Visual Assets

### Files Provided:

No visual assets provided.

### Visual Insights:

Not applicable - no visual files found in the visuals folder.

## Requirements Summary

### Functional Requirements

**Core Search Functionality:**
- Full-text search using PostgreSQL's tsvector/tsquery capabilities
- Search across multiple fields: task titles, task descriptions, subtask titles, and task comments
- Search across all workspaces accessible to the user
- Display workspace name for each task in search results

**Search Interface:**
- Navigation bar search input with live results dropdown
- Dropdown shows preview results as user types
- "View all results" link in dropdown to navigate to full search results page
- Dedicated search results page for comprehensive result viewing

**Search Results Display:**
- Show text snippets (approximately 150 characters) with matched search terms highlighted
- Display workspace name for each result
- Support for multiple sorting options:
  - Relevance (default)
  - Due date
  - Priority
  - Created date
- Support for filtering by:
  - Project
  - Tags
  - Status (active/completed)
  - Priority

**Advanced Search Features:**
- Advanced search operators: AND, OR, NOT
- Regex support for pattern matching
- Saved search queries functionality
- Recent searches stored persistently in database (accessible across sessions/devices)

**User Experience:**
- Live search results update as user types in navigation bar
- Highlighted search terms in result snippets for easy scanning
- Clear indication of which workspace each result belongs to
- Intuitive sorting and filtering controls on search results page

### Reusability Opportunities

No specific existing components identified for reuse. Implementation should:
- Follow existing UI patterns and design consistency
- Adhere to current navigation bar styling and behavior
- Use standard Workstate UI components and conventions
- Maintain visual consistency with existing page layouts

### Scope Boundaries

**In Scope:**
- PostgreSQL full-text search implementation (tsvector/tsquery)
- Live search dropdown in navigation bar
- Full search results page with sorting and filtering
- Search across task titles, descriptions, subtask titles, and comments
- Cross-workspace search with workspace identification
- Search term highlighting in result snippets
- Advanced search operators (AND, OR, NOT)
- Regex pattern matching support
- Saved search queries
- Persistent recent searches (database storage)
- Sorting by relevance, due date, priority, created date
- Filtering by project, tags, status, priority

**Out of Scope:**
- No features explicitly excluded
- All originally proposed advanced features are included in scope

### Technical Considerations

**Database & Search:**
- Use PostgreSQL full-text search (tsvector/tsquery)
- Index task titles, descriptions, subtask titles, and comments for search performance
- Store recent searches in database for cross-session/device persistence
- Store saved search queries in database with user association

**Performance:**
- Implement debouncing for live search dropdown to avoid excessive queries
- Optimize PostgreSQL full-text search indexes
- Consider pagination for search results to handle large result sets

**Integration Points:**
- Navigation bar component for search input integration
- Workspace access control to filter search results appropriately
- Task, subtask, and comment models for search indexing
- User model for storing saved searches and search history

**UI/UX Patterns:**
- HTMX for live search dropdown updates
- Alpine.js for dropdown state management
- Tailwind CSS for consistent styling
- Server-side rendering for search results page
- Accessibility considerations for keyboard navigation in search dropdown

**Security & Privacy:**
- Respect workspace permissions - only show tasks user has access to
- Sanitize search inputs to prevent SQL injection
- Validate advanced search operators and regex patterns
- Associate saved searches and history with authenticated user only
