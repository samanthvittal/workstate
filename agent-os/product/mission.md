# Product Mission

## Pitch

Workstate is a self-hosted productivity platform that helps individuals and small teams understand their work by connecting what they plan to do with how long it actually takes. By treating tasks and time as equally important first-class citizens, Workstate provides the clarity needed to make better decisions about priorities, capacity, and progress—all while respecting your privacy and giving you complete control over your data.

## Users

### Primary Customers

- **Solo Knowledge Workers**: Developers, designers, writers, and consultants who need to track both their work commitments and time spent
- **Small Teams (2-10 people)**: Startups, agencies, and small businesses needing collaborative task and time management without vendor lock-in
- **Privacy-Conscious Professionals**: Users who want complete data ownership and prefer self-hosted solutions over SaaS
- **Technical Users**: Developers and IT professionals comfortable with self-hosting who want an extensible, open-source platform

### User Personas

**Alex** (28-45)
- **Role:** Freelance Software Developer / Consultant
- **Context:** Manages multiple client projects simultaneously, bills by the hour
- **Pain Points:**
  - Juggling tasks across multiple projects without clear time estimates
  - Forgetting to track billable hours, leading to revenue loss
  - Needing to switch between separate task manager and time tracker tools
  - Concerns about data privacy with SaaS tools tracking work patterns
- **Goals:**
  - Track all tasks and time in one unified place
  - Understand actual vs. estimated time to improve future estimates
  - Generate accurate time reports for client billing
  - Own and control all work data on personal infrastructure

**Jordan** (30-50)
- **Role:** Startup Founder / Small Team Lead
- **Context:** Leading a team of 5-8 people on product development
- **Pain Points:**
  - Team using disconnected tools for tasks and time tracking
  - No visibility into how long tasks actually take vs. estimates
  - Paying monthly fees per user for multiple SaaS tools
  - Data locked in proprietary systems with no portability
- **Goals:**
  - Unified platform for team task and time management
  - Better capacity planning based on real data
  - Reduce tool sprawl and subscription costs
  - Self-host on company infrastructure for compliance and control

**Sam** (25-40)
- **Role:** Product Manager / Individual Contributor
- **Context:** Organizing personal and professional work
- **Pain Points:**
  - Difficulty understanding where time actually goes each day
  - No clear connection between tasks completed and time invested
  - Wants privacy but values modern, polished user experience
  - Tired of feature bloat in productivity apps
- **Goals:**
  - Simple, focused tool that does one thing exceptionally well
  - Clear insights into productivity patterns
  - No tracking or analytics by the tool vendor
  - Clean, intuitive interface without unnecessary complexity

## The Problem

### The Intent-Reality Gap

Most people know what they plan to work on, but have little understanding of how long things actually take. This creates a fundamental disconnect between intent (tasks) and reality (time). Without bridging this gap, planning becomes guesswork, schedules become unrealistic, and capacity remains invisible.

**Traditional approaches fail because:**
- Task managers focus only on what to do, completely ignoring duration and capacity
- Time trackers record hours but don't connect them meaningfully to outcomes or goals
- Using separate tools creates friction, leading to incomplete data and context switching
- Proprietary SaaS solutions lock in data and require ongoing per-user subscriptions
- Privacy concerns arise when cloud-based tools store and potentially analyze work data

**The result:**
- Poor time estimates that compound into unrealistic schedules and missed deadlines
- Inability to learn from past work to improve future planning
- No clear view of actual capacity vs. commitments, leading to burnout
- Privacy concerns with cloud-based tools storing sensitive work data
- Subscription costs that scale with team size and tool proliferation

**Our Solution:**

Workstate unifies task management and time tracking in a single self-hosted platform where tasks and time are treated as equal first-class concepts. Every task can have time tracked against it. Every time entry connects to a task. This creates a continuous feedback loop where you see not just what you did, but how long it actually took—enabling better planning, realistic commitments, and continuous improvement.

## Differentiators

### Unified Task-Time Model

Unlike tools that bolt on time tracking as an afterthought or treat task management as a secondary feature, Workstate treats tasks and time as equal first-class concepts from the ground up. This isn't just about UI convenience—the data model itself is designed around the relationship between intent (tasks) and execution (time).

**This results in:**
- Natural workflow where tracking time on tasks feels integrated, not bolted on
- Rich insights showing estimated vs. actual time at every level (task, project, user)
- Ability to learn from history to improve future estimates
- Clear visibility into capacity and workload based on real data
- Continuous feedback loop between planning and execution

### Self-Hosted and Privacy-First

While competitors focus on SaaS convenience and recurring revenue, Workstate prioritizes data ownership and privacy. You run it on your own infrastructure, your data never leaves your control, and there's no vendor lock-in or feature upselling.

**This results in:**
- Complete data ownership and control with no third-party access
- No monthly per-user fees or subscription creep
- Ability to customize and extend for specific needs
- Compliance with strict data residency requirements
- No telemetry, tracking, or monetization of user data
- Transparent open-source codebase you can audit and modify

### Clarity Over Complexity

Workstate follows a philosophy of clarity over complexity. Simple, readable solutions over unnecessary abstractions. Modern UX without heavyweight frameworks. This approach makes the platform approachable for users and maintainable for developers.

**This results in:**
- Clean, focused interface without feature bloat
- Clear mental model that's easy to learn and adopt
- Faster performance and smaller resource footprint
- Lower barrier for Python developers to contribute and customize
- Simpler deployment and maintenance

### Python-First, Modern Stack

Unlike React/Vue-heavy alternatives requiring extensive JavaScript expertise, Workstate uses HTMX and Alpine.js for interactivity while keeping the core in Python/Django. This provides a modern, dynamic user experience without the complexity overhead of a full SPA framework.

**This results in:**
- Lower barrier for Python/Django developers to contribute and customize
- Simpler deployment and maintenance with server-side rendering
- Smaller bundle sizes and faster page loads
- Better SEO and accessibility out of the box
- Reduced frontend/backend coordination complexity

### Extensible by Design

Rather than trying to be an all-in-one platform, Workstate focuses on doing task and time management exceptionally well, with clear APIs and integration points for extending functionality.

**This results in:**
- Lean, maintainable codebase without feature bloat
- Clear boundaries and separation of concerns
- Open REST API for custom integrations and tooling
- Plugin architecture for optional features (AI suggestions, advanced automations)
- Easy integration with existing workflows and tools

## Key Features

### Core Features

- **Task Management:** Create, organize, and prioritize tasks with projects, due dates, priorities (P1-P4), tags, and subtasks
- **Time Tracking:** Start/stop timers, manual time entry, running timer display, edit and manage time entries linked to tasks and projects
- **Smart Input:** Natural language parsing for quick task creation (e.g., "Deploy API tomorrow 2pm p1 #backend")
- **Multiple Views:** List, board (Kanban), calendar, and timesheet views to visualize work in different ways
- **Flexible Organization:** Projects with sections, favorites, color coding, and hierarchical structure
- **Search & Filter:** Global search across tasks and projects with quick filters and saved filter configurations

### Collaboration Features

- **Workspaces:** Separate personal and team spaces with isolated data and independent configurations
- **Task Assignment:** Assign tasks to team members, track ownership, and filter by assignee
- **Comments & Activity:** Threaded discussions on tasks, activity feeds showing team actions and updates
- **Notifications:** In-app and email notifications for assignments, comments, due dates, and reminders
- **Sharing:** Share projects with granular permissions (view, comment, edit, admin)
- **Team Insights:** View team workload distribution, time reports, and productivity analytics

### Advanced Features

- **Time Reports:** Detailed and summary reports by project, task, user, and date range with export to CSV/PDF
- **Productivity Analytics:** Track tasks completed, time spent, goal progress, streaks, and trends over time
- **Recurring Tasks:** Flexible recurrence patterns (daily, weekly, monthly, yearly) for repeating work
- **Pomodoro Timer:** Built-in focus timer with customizable work/break intervals and session tracking
- **Task Templates:** Save and reuse task structures, duplicate tasks with attributes, clone entire projects
- **Subtasks & Checklists:** Unlimited nested subtask depth and simple checkbox lists within task descriptions
- **File Attachments:** Upload files to tasks with configurable storage (local filesystem or S3-compatible)
- **Task Dependencies:** Link related tasks with blocks/blocked-by relationships
- **Bulk Operations:** Multi-select tasks for batch actions (complete, delete, move, change priority, add tags)
- **Custom Filters:** Build advanced filters with multiple conditions (AND/OR logic) and save configurations
- **Time Goals:** Set daily/weekly time goals and project budgets with visual progress indicators

### Integrations & Platform Support

- **REST API:** Full-featured API for integrations and custom tooling with token authentication
- **Calendar Integration:** Google Calendar and Outlook Calendar two-way sync, iCal feed generation
- **Import/Export:** Migrate data from Todoist and Toggl, CSV import/export, complete data backup and restore
- **Webhooks:** Outgoing webhooks for events to integrate with Slack, Discord, Zapier, n8n
- **Offline Support:** Progressive Web App (PWA) works offline and syncs when connected
- **Cross-Platform:** Responsive web app, desktop apps (Tauri for Windows/Mac/Linux), mobile PWA, browser extensions
- **GitHub/GitLab:** Link tasks to issues and commits for development workflow integration
