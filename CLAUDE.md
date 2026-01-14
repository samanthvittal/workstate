# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Workstate is a self-hosted, open-source task management and time tracking application that treats tasks and time as first-class citizens. The project is in early development with a focus on establishing clear architecture and standards before implementation.

**Core Philosophy:**
- Clarity over complexity
- Self-hosted first, privacy-respecting
- Simple, readable solutions over unnecessary abstractions
- Tasks represent intent, time represents reality

## Tech Stack

**Backend:**
- Python 3.11+ with Django 5.x
- Django REST Framework 3.15+ for API
- PostgreSQL 15+ (primary database)
- Redis 7+ (caching, sessions, Celery broker)
- Celery 5.x for background jobs
- Django Channels 4.x + Daphne for WebSocket/real-time features

**Frontend:**
- HTMX 1.9+ (dynamic UX without SPA complexity)
- Alpine.js 3.x (lightweight reactivity for modals, dropdowns)
- Tailwind CSS 3.x via django-tailwind 3.x
- Server-side rendering with Django templates

**Development Tools:**
- pytest for testing
- ruff for linting and formatting
- bandit for security scanning
- Docker & Docker Compose for deployment

## Development Commands

Since the project is in early development, standard Django commands will apply once implementation begins:

```bash
# Development server (once Django is set up)
python manage.py runserver

# Run tests
pytest

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Linting and formatting
ruff check .
ruff format .

# Security scanning
bandit -r .
```

## Architecture & Code Organization

### Agent-OS Framework

This project uses **agent-os**, an AI-native development framework. Key directories:

- **`agent-os/specs/`** - Project specifications (900+ line spec defining 273 features)
- **`agent-os/standards/`** - Comprehensive coding standards organized by domain:
  - `global/` - Cross-cutting concerns (style, commenting, error handling, validation)
  - `backend/` - Django/Python patterns (models, API, queries, migrations)
  - `frontend/` - UI standards (components, CSS, accessibility, responsive design)
  - `testing/` - Test writing philosophy
- **`.claude/agents/`** - AI agent configurations for development tasks
- **`.claude/commands/`** - Custom Claude Code commands (orchestrate-tasks, create-tasks, shape-spec, etc.)

### Standards to Follow

Before making changes, review relevant standards in `agent-os/standards/`:

1. **Code Style** (`global/coding-style.md`):
   - Self-documenting code with clear naming
   - Small, focused functions (single responsibility)
   - Meaningful, non-abbreviated variable names
   - Remove dead code

2. **API Design** (`backend/api.md`):
   - RESTful resource-based URLs
   - Appropriate HTTP status codes
   - Query parameters for filtering/sorting/pagination
   - User-friendly error messages

3. **Database Models** (`backend/models.md`):
   - All models have `created_at` and `updated_at` timestamps
   - Strong database constraints for data integrity
   - Index foreign keys and frequently queried columns
   - Defense-in-depth validation (model + database layers)

4. **Frontend Components** (`frontend/components.md`):
   - HTMX for dynamic interactions
   - Alpine.js for client-side state
   - Tailwind utility classes for styling
   - Minimize custom JavaScript

5. **Testing** (`testing/test-writing.md`):
   - Test critical paths and primary workflows
   - Focus on behavior, not implementation
   - Mock external dependencies
   - Keep tests fast (milliseconds)

### Key Architectural Decisions

- **Monolithic Django application** (not microservices)
- **PostgreSQL as source of truth** with strong constraints
- **Server-side rendering** with HTMX (not SPA)
- **Minimal JavaScript** - keep stack in Python for Django developers
- **Background jobs via Celery** for async operations
- **WebSocket support via Channels** for real-time features

## Feature Organization

The project specification defines 273 features across 10 categories:
1. Task Management (37 features)
2. Project Management (18 features)
3. Time Tracking (44 features)
4. Views & Navigation (36 features)
5. Collaboration (24 features)
6. Automation & AI (21 features)
7. Reporting & Analytics (23 features)
8. Integrations (24 features)
9. Platforms & Apps (26 features)
10. Settings & Customization (20 features)

Reference `agent-os/specs/workstate/spec.md` for detailed feature specifications.

## Development Workflow

1. **Read the spec first** - `agent-os/specs/workstate/spec.md` contains detailed requirements
2. **Follow the standards** - Review relevant files in `agent-os/standards/` before coding
3. **Feature branches** - Use `feature/your-change` naming
4. **Focused commits** - Clear, well-described commits
5. **Test where applicable** - Critical paths and primary workflows
6. **No over-engineering** - Simple solutions, avoid premature abstractions

## Error Handling Patterns

- User-friendly error messages (never expose technical details)
- Server-side validation is authoritative
- Client-side validation for UX only
- Specific exception types for different error conditions
- Centralized error handling at API layer
- Business rule validation at application layer

## Non-Goals (Important)

To stay focused, Workstate intentionally does NOT aim to:
- Clone existing proprietary products
- Replicate proprietary UX or workflows
- Offer built-in SaaS hosting initially
- Track users or monetize data
- Compete on marketing-driven feature bloat
- Reverse engineer proprietary features

## Project Status

**Current Phase:** Early Development - Foundation architecture
- Standards and specifications are defined
- Implementation has not yet begun
- Focus is on establishing clear patterns before coding

**Deployment Roadmap:**
- Phase 1 (MVP): Core task & time tracking
- Phase 2: Enhanced UX improvements
- Phase 3: Collaboration & multi-platform
- Phase 4: Advanced features
- Phase 5: Enterprise features & scalability

## License

Apache License 2.0 - See LICENSE file for details.
