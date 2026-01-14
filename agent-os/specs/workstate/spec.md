# Workstate - Open Source Task & Time Management

**License**: Apache 2.0  
**Deployment**: Self-hosted  
**Tech Stack**: Python, Django, PostgreSQL, HTMX, Tailwind CSS  
**Repository**: [github.com/samanthvittal/workstate](https://github.com/samanthvittal/workstate)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Feature Categories](#feature-categories)
4. [Complete Feature List](#complete-feature-list)
5. [Phased Implementation Plan](#phased-implementation-plan)
6. [Technical Architecture](#technical-architecture)
7. [Frontend Architecture](#frontend-architecture)
8. [Data Models (Django)](#data-models-django)
9. [API Specification](#api-specification)
10. [Deployment Guide](#deployment-guide)
11. [Contributing](#contributing)

---

## Project Overview

Workstate is a self-hosted, open-source productivity application that combines:

- **Task Management** (inspired by Todoist) - Organize work and life with projects, tasks, priorities, and deadlines
- **Time Tracking** (inspired by Toggl Track) - Track time spent on tasks and projects with detailed reporting

### Core Principles

- **Self-hosted & Privacy-first** - Your data stays on your servers
- **No vendor lock-in** - Full data ownership and portability
- **Python-first** - Full stack Python with Django, minimal JavaScript
- **Cross-platform** - Web (primary), Desktop, Mobile, Browser Extension
- **Offline-first** - Work without internet, sync when connected
- **Extensible** - Plugin architecture for custom integrations
- **Simple deployment** - Docker-first with minimal configuration
- **Enterprise-ready** - Supports API Gateway integration when needed

### Why Self-Hosted?

- Complete data ownership and privacy
- No subscription fees
- Customize to your needs
- Integrate with internal systems
- Comply with data residency requirements
- No external dependencies for core functionality

### Why Apache 2.0?

- Permissive license allowing commercial use
- Patent protection clause
- Clear contribution terms
- Compatible with most other open-source licenses
- Suitable for enterprise adoption

---

## Technology Stack

### Core Backend Stack

| Component             | Technology            | Version | Rationale                                 |
| --------------------- | --------------------- | ------- | ----------------------------------------- |
| **Language**          | Python                | 3.11+   | Modern features, type hints, performance  |
| **Backend Framework** | Django                | 5.x     | Batteries-included, mature, excellent ORM |
| **API Framework**     | Django REST Framework | 3.15+   | API for mobile/desktop apps, integrations |
| **Database**          | PostgreSQL            | 15+     | Robust, JSON support, full-text search    |
| **Cache**             | Redis                 | 7+      | Session storage, caching                  |
| **Task Queue**        | Celery                | 5.x     | Background jobs, scheduled tasks          |
| **Message Broker**    | Redis                 | 7+      | Celery broker (or RabbitMQ)               |
| **Real-time**         | Django Channels       | 4.x     | WebSocket support for live updates        |
| **Search**            | PostgreSQL FTS        | -       | Built-in full-text search                 |

### Frontend Stack (Python-First)

| Component             | Technology         | Version | Rationale                                    |
| --------------------- | ------------------ | ------- | -------------------------------------------- |
| **Templating**        | Django Templates   | -       | Server-side rendering, Python-native         |
| **Interactivity**     | HTMX               | 1.9+    | Dynamic UX without JavaScript frameworks     |
| **Client-side Logic** | Alpine.js          | 3.x     | Lightweight reactivity for modals, dropdowns |
| **Styling**           | Tailwind CSS       | 3.x     | Utility-first, highly customizable           |
| **Build Tool**        | django-tailwind    | 3.x     | Tailwind integration for Django              |
| **Icons**             | Heroicons / Lucide | -       | SVG icons, Tailwind-compatible               |
| **Charts**            | Chart.js           | 4.x     | Lightweight charting (via CDN)               |

### Why This Frontend Stack?

#### Tailwind CSS over Bootstrap

| Aspect                 | Tailwind CSS                    | Bootstrap                |
| ---------------------- | ------------------------------- | ------------------------ |
| **File Size**          | ~10-20KB (purged)               | ~150KB+                  |
| **Customization**      | Highly flexible                 | Opinionated, limited     |
| **Design Uniqueness**  | Easy to create unique designs   | Sites often look similar |
| **Learning Curve**     | Steeper initially               | Easier to start          |
| **Modern Approach**    | Utility-first, current standard | Component-based, mature  |
| **Django Integration** | django-tailwind (excellent)     | django-bootstrap5 (good) |
| **HTMX Compatibility** | Perfect                         | Good                     |
| **Maintenance**        | Active, growing ecosystem       | Stable, slower updates   |

**Verdict**: Tailwind CSS provides more flexibility, smaller builds, and better aligns with modern web development practices. The utility-first approach works exceptionally well with Django templates and HTMX.

#### HTMX over JavaScript Frameworks

| Aspect                        | HTMX + Django          | React/Vue                  |
| ----------------------------- | ---------------------- | -------------------------- |
| **Complexity**                | Low                    | High                       |
| **Python Developer Friendly** | Yes (minimal JS)       | No (requires JS expertise) |
| **Server-Side Rendering**     | Native                 | Requires SSR setup         |
| **Bundle Size**               | ~14KB                  | 100KB+                     |
| **Learning Curve**            | Low for Django devs    | High                       |
| **SEO**                       | Excellent (SSR)        | Requires configuration     |
| **State Management**          | Server-side (Django)   | Client-side (complex)      |
| **Real-time Updates**         | Django Channels + HTMX | WebSocket + state sync     |

**Verdict**: HTMX allows building dynamic, modern UIs while keeping the entire stack in Python. Perfect for teams who want to minimize JavaScript complexity.

### Desktop & Mobile

| Platform              | Technology              | Rationale                |
| --------------------- | ----------------------- | ------------------------ |
| **Desktop**           | Tauri (Rust + WebView)  | Lightweight, uses web UI |
| **Mobile**            | PWA (Primary)           | Works on all devices     |
| **Mobile Native**     | Kivy / BeeWare (Python) | Optional, Python-native  |
| **Browser Extension** | Web Extension API       | Timer, quick add         |

### Optional Enterprise Components

| Component         | Technology             | When Needed                 |
| ----------------- | ---------------------- | --------------------------- |
| **API Gateway**   | Kong / Traefik / nginx | High-traffic, microservices |
| **Load Balancer** | nginx / HAProxy        | Multiple instances          |
| **Monitoring**    | Prometheus + Grafana   | Production observability    |
| **Logging**       | ELK Stack / Loki       | Centralized logging         |
| **SSO/SAML**      | django-allauth + SAML  | Enterprise authentication   |

---

## Feature Categories

| Category                     | Description                                 | Feature Count |
| ---------------------------- | ------------------------------------------- | ------------- |
| **Task Management**          | Creating, organizing, and completing tasks  | 37            |
| **Project Management**       | Grouping tasks into projects and folders    | 18            |
| **Time Tracking**            | Recording time spent on work                | 44            |
| **Views & Navigation**       | Different ways to visualize and access data | 36            |
| **Collaboration**            | Multi-user features and sharing             | 24            |
| **Automation & AI**          | Smart features and automated workflows      | 21            |
| **Reporting & Analytics**    | Insights and data visualization             | 23            |
| **Integrations**             | Third-party connections and API             | 24            |
| **Platforms & Apps**         | Where the app runs                          | 26            |
| **Settings & Customization** | User preferences and personalization        | 20            |
| **Total**                    |                                             | **273**       |

---

## Complete Feature List

### 1. Task Management

#### 1.1 Task Creation & Editing

| ID   | Feature           | Description                                         | Priority |
| ---- | ----------------- | --------------------------------------------------- | -------- |
| T001 | Basic Task CRUD   | Create, read, update, delete tasks                  | P0       |
| T002 | Task Title        | Primary task identifier (required)                  | P0       |
| T003 | Task Description  | Rich text description with markdown support         | P0       |
| T004 | Due Date          | Date when task is due                               | P0       |
| T005 | Due Time          | Specific time for deadline                          | P0       |
| T006 | Priority Levels   | 4 levels (P1=Urgent, P2=High, P3=Medium, P4=Low)    | P0       |
| T007 | Labels/Tags       | Multiple tags per task for categorization           | P0       |
| T008 | Subtasks          | Nested tasks within a parent task (unlimited depth) | P1       |
| T009 | Task Duration     | Estimated time to complete (minutes/hours)          | P1       |
| T010 | Task Comments     | Threaded discussion on tasks                        | P1       |
| T011 | File Attachments  | Attach files to tasks (configurable storage)        | P2       |
| T012 | Task Templates    | Save and reuse task structures                      | P2       |
| T013 | Task Dependencies | Link tasks (blocks/blocked by relationships)        | P3       |
| T014 | Checklists        | Simple checkbox lists within task description       | P1       |

#### 1.2 Task Scheduling

| ID   | Feature                  | Description                                                         | Priority |
| ---- | ------------------------ | ------------------------------------------------------------------- | -------- |
| T020 | Recurring Tasks          | Repeat patterns: daily, weekly, monthly, yearly                     | P1       |
| T021 | Advanced Recurrence      | "Every 2 weeks", "Mon/Wed/Fri", "Last day of month", "3rd Thursday" | P2       |
| T022 | Start Dates              | When task becomes active/visible                                    | P2       |
| T023 | Reminders                | Notification before due date/time                                   | P1       |
| T024 | Multiple Reminders       | Set several reminders per task                                      | P2       |
| T025 | Location-based Reminders | Trigger based on GPS location (mobile)                              | P3       |
| T026 | Snooze                   | Postpone reminder to later (1hr, 3hr, tomorrow, etc.)               | P1       |
| T027 | Defer to Date            | Move task to specific future date                                   | P1       |

#### 1.3 Task Organization

| ID   | Feature         | Description                                         | Priority |
| ---- | --------------- | --------------------------------------------------- | -------- |
| T030 | Task Assignment | Assign tasks to workspace members                   | P1       |
| T031 | Task Sections   | Group tasks within a project into sections          | P1       |
| T032 | Task Ordering   | Manual drag-drop reordering within section          | P0       |
| T033 | Task Moving     | Move tasks between projects/sections                | P0       |
| T034 | Bulk Operations | Multi-select and batch edit/move/delete/complete    | P1       |
| T035 | Duplicate Task  | Clone task with all attributes (optional: subtasks) | P1       |
| T036 | Task Archive    | Archive completed tasks (separate from delete)      | P1       |
| T037 | Task History    | Audit log of changes made to a task                 | P2       |

---

### 2. Project Management

#### 2.1 Project Basics

| ID   | Feature             | Description                            | Priority |
| ---- | ------------------- | -------------------------------------- | -------- |
| P001 | Project CRUD        | Create, read, update, delete projects  | P0       |
| P002 | Project Name        | Primary project identifier (required)  | P0       |
| P003 | Project Description | Details about the project (markdown)   | P1       |
| P004 | Project Color       | Color coding for visual identification | P0       |
| P005 | Project Icon        | Emoji or icon for quick recognition    | P2       |
| P006 | Project Favorites   | Star/pin important projects to top     | P1       |
| P007 | Project Archive     | Archive completed/inactive projects    | P1       |

#### 2.2 Project Organization

| ID   | Feature             | Description                                  | Priority |
| ---- | ------------------- | -------------------------------------------- | -------- |
| P010 | Project Folders     | Nest projects in folders/groups              | P2       |
| P011 | Project Hierarchy   | Parent/child project relationships           | P3       |
| P012 | Project Ordering    | Manual drag-drop ordering of projects        | P1       |
| P013 | Project Sections    | Divide project into collapsible sections     | P1       |
| P014 | Project Templates   | Save and reuse project structures with tasks | P2       |
| P015 | Project Duplication | Clone entire project with all tasks          | P2       |

#### 2.3 Project Settings

| ID   | Feature              | Description                                      | Priority |
| ---- | -------------------- | ------------------------------------------------ | -------- |
| P020 | Default View Setting | Set preferred view per project                   | P2       |
| P021 | View Persistence     | Remember last used view per user per project     | P1       |
| P022 | View Customization   | Configure columns, sorting, grouping per project | P2       |

---

### 3. Time Tracking

#### 3.1 Time Entry Methods

| ID    | Feature                 | Description                                  | Priority |
| ----- | ----------------------- | -------------------------------------------- | -------- |
| TT001 | Start/Stop Timer        | Real-time timer with one-click start/stop    | P0       |
| TT002 | Manual Time Entry       | Enter start time + end time, or duration     | P0       |
| TT003 | Duration-Only Mode      | Log hours without specific start/end times   | P1       |
| TT004 | Running Timer Display   | Show active timer in header across all views | P0       |
| TT005 | Timer Description       | Add/edit notes on running timer              | P0       |
| TT006 | Timer Project/Task Link | Associate timer with project and/or task     | P0       |
| TT007 | Edit Running Timer      | Modify start time while timer is running     | P1       |
| TT008 | Discard Timer           | Cancel running timer without saving          | P0       |
| TT009 | Continue Previous       | Resume/continue a previous time entry        | P1       |

#### 3.2 Time Entry Management

| ID    | Feature                | Description                               | Priority |
| ----- | ---------------------- | ----------------------------------------- | -------- |
| TT010 | Time Entry CRUD        | Create, read, update, delete time entries | P0       |
| TT011 | Time Entry Description | Notes about what was done                 | P0       |
| TT012 | Time Entry Tags        | Categorize time entries with labels       | P1       |
| TT013 | Time Entry Project     | Associate entry with a project            | P0       |
| TT014 | Time Entry Task        | Associate entry with a specific task      | P1       |
| TT015 | Bulk Time Edit         | Edit multiple entries at once             | P2       |
| TT016 | Duplicate Entry        | Clone a time entry to new date/time       | P1       |
| TT017 | Split Entry            | Divide one entry into multiple entries    | P2       |
| TT018 | Merge Entries          | Combine multiple consecutive entries      | P2       |

#### 3.3 Automated Time Tracking

| ID    | Feature                   | Description                                  | Priority |
| ----- | ------------------------- | -------------------------------------------- | -------- |
| TT020 | Idle Detection            | Detect system inactivity and prompt user     | P1       |
| TT021 | Idle Time Options         | Keep, discard, or subtract idle time         | P1       |
| TT022 | Desktop Activity Tracking | Track apps/websites (opt-in, local only)     | P3       |
| TT023 | Activity Timeline         | Visual timeline of tracked activities        | P3       |
| TT024 | Calendar Integration      | View calendar events, one-click to track     | P2       |
| TT025 | Auto-start Timer          | Start when opening specific apps/websites    | P3       |
| TT026 | Keyword Triggers          | Auto-assign project/task based on keywords   | P3       |
| TT027 | Tracking Reminders        | Remind if no timer running during work hours | P2       |

#### 3.4 Pomodoro & Focus

| ID    | Feature          | Description                                  | Priority |
| ----- | ---------------- | -------------------------------------------- | -------- |
| TT030 | Pomodoro Timer   | Standard 25-min work + 5-min break cycle     | P2       |
| TT031 | Custom Pomodoro  | Configurable work/break/long-break durations | P2       |
| TT032 | Pomodoro Counter | Track completed pomodoros per day/task       | P2       |
| TT033 | Focus Mode       | Minimize UI distractions during active timer | P3       |
| TT034 | Break Reminders  | Notify when to take breaks                   | P2       |

#### 3.5 Goals & Targets

| ID    | Feature            | Description                        | Priority |
| ----- | ------------------ | ---------------------------------- | -------- |
| TT040 | Daily Time Goal    | Target hours per day               | P2       |
| TT041 | Weekly Time Goal   | Target hours per week              | P2       |
| TT042 | Project Time Goal  | Target/budget hours per project    | P2       |
| TT043 | Goal Progress      | Visual progress indicator          | P2       |
| TT044 | Goal Notifications | Alert when goal reached or at risk | P3       |

---

### 4. Views & Navigation

#### 4.1 Task Views

| ID   | Feature             | Description                                   | Priority |
| ---- | ------------------- | --------------------------------------------- | -------- |
| V001 | List View           | Traditional vertical list with inline editing | P0       |
| V002 | Board View (Kanban) | Columns with drag-drop cards                  | P1       |
| V003 | Calendar View       | Month/week/day grid with tasks as events      | P2       |
| V004 | Timeline/Gantt View | Tasks on timeline showing dependencies        | P3       |
| V005 | Table View          | Spreadsheet-like with sortable columns        | P2       |

#### 4.2 Smart Views

| ID   | Feature        | Description                     | Priority |
| ---- | -------------- | ------------------------------- | -------- |
| V010 | Today View     | Tasks due today + overdue tasks | P0       |
| V011 | Upcoming View  | Tasks for next 7/14/30 days     | P0       |
| V012 | Inbox          | Tasks without a project         | P0       |
| V013 | Completed View | Recently completed tasks        | P1       |
| V014 | Assigned to Me | Tasks assigned to current user  | P1       |
| V015 | Labels View    | Browse/filter tasks by label    | P1       |
| V016 | Priority View  | Tasks grouped by priority level | P1       |

#### 4.3 Time Tracking Views

| ID   | Feature            | Description                              | Priority |
| ---- | ------------------ | ---------------------------------------- | -------- |
| V020 | Timer View         | Active timer display with recent entries | P0       |
| V021 | Timesheet View     | Weekly grid for quick time entry         | P1       |
| V022 | Calendar Time View | Time entries displayed on calendar       | P2       |
| V023 | Timeline View      | Visual timeline of day's activities      | P2       |
| V024 | Entries List       | Filterable list of all time entries      | P0       |

#### 4.4 Filters & Search

| ID   | Feature               | Description                               | Priority |
| ---- | --------------------- | ----------------------------------------- | -------- |
| V030 | Global Search         | Search across tasks, projects, entries    | P0       |
| V031 | Quick Filters         | Predefined filter buttons                 | P1       |
| V032 | Custom Filters        | Build filters with multiple conditions    | P1       |
| V033 | Saved Filters         | Save and name filter configurations       | P1       |
| V034 | Filter Query Language | Text-based filter syntax                  | P2       |
| V035 | Recent Searches       | History of recent search queries          | P2       |
| V036 | Search Suggestions    | Autocomplete with projects, labels, tasks | P2       |

#### 4.5 Sorting & Grouping

| ID   | Feature            | Description                              | Priority |
| ---- | ------------------ | ---------------------------------------- | -------- |
| V040 | Sort by Field      | Due date, priority, title, created, etc. | P0       |
| V041 | Sort Direction     | Ascending/descending toggle              | P0       |
| V042 | Multi-level Sort   | Sort by primary, then secondary field    | P2       |
| V043 | Group by Field     | Project, priority, date, label, assignee | P1       |
| V044 | Collapsible Groups | Expand/collapse grouped sections         | P1       |

---

### 5. Collaboration

#### 5.1 User Management

| ID   | Feature             | Description                              | Priority |
| ---- | ------------------- | ---------------------------------------- | -------- |
| C001 | User Registration   | Email/password signup with verification  | P0       |
| C002 | User Authentication | Login/logout with session management     | P0       |
| C003 | User Profile        | Name, avatar, bio, timezone, preferences | P0       |
| C004 | Password Reset      | Forgot password email flow               | P0       |
| C005 | OAuth Login         | Google, GitHub, GitLab, Microsoft        | P2       |
| C006 | Two-Factor Auth     | TOTP-based 2FA                           | P2       |

#### 5.2 Workspaces & Teams

| ID   | Feature             | Description                            | Priority |
| ---- | ------------------- | -------------------------------------- | -------- |
| C010 | Workspaces          | Isolated spaces for different contexts | P1       |
| C011 | Personal Workspace  | Default workspace for each user        | P0       |
| C012 | Team Workspaces     | Shared workspace for collaboration     | P2       |
| C013 | Workspace Switching | Quick switch between workspaces        | P1       |
| C014 | Team Creation       | Create and configure teams             | P2       |
| C015 | Team Members        | Invite, add, remove team members       | P2       |
| C016 | Team Roles          | Owner, Admin, Member, Guest roles      | P2       |

#### 5.3 Sharing & Permissions

| ID   | Feature            | Description                               | Priority |
| ---- | ------------------ | ----------------------------------------- | -------- |
| C020 | Project Sharing    | Share project with specific users         | P1       |
| C021 | Share via Link     | Generate public/private shareable links   | P2       |
| C022 | Permission Levels  | View-only, Comment, Edit, Admin           | P2       |
| C023 | Guest Access       | Limited access for external collaborators | P2       |
| C024 | Transfer Ownership | Hand over project ownership               | P2       |

#### 5.4 Communication

| ID   | Feature              | Description                          | Priority |
| ---- | -------------------- | ------------------------------------ | -------- |
| C030 | Task Comments        | Threaded discussion on tasks         | P1       |
| C031 | @Mentions            | Mention users in comments            | P2       |
| C032 | Comment Reactions    | Emoji reactions to comments          | P3       |
| C033 | Activity Feed        | Stream of workspace/project activity | P2       |
| C034 | In-app Notifications | Notification center with read/unread | P1       |
| C035 | Email Notifications  | Configurable email alerts            | P2       |
| C036 | Push Notifications   | Browser/mobile push alerts           | P2       |

---

### 6. Automation & AI

#### 6.1 Smart Input (NLP)

| ID   | Feature                  | Description                                  | Priority |
| ---- | ------------------------ | -------------------------------------------- | -------- |
| A001 | Natural Language Parsing | Parse "Buy milk tomorrow 5pm p1 #shopping"   | P1       |
| A002 | Date Parsing             | "today", "tomorrow", "next monday", "jan 15" | P1       |
| A003 | Time Parsing             | "at 5pm", "14:00", "morning", "evening"      | P1       |
| A004 | Priority Parsing         | "p1", "p2", "!", "!!", "urgent"              | P1       |
| A005 | Project Parsing          | "#projectname" syntax                        | P1       |
| A006 | Label Parsing            | "@labelname" syntax                          | P1       |
| A007 | Duration Parsing         | "2h", "30m", "1h30m"                         | P2       |
| A008 | Assignee Parsing         | "+username" to assign task                   | P2       |
| A009 | Recurring Parsing        | "every monday", "daily", "weekly"            | P2       |

#### 6.2 Quick Actions

| ID   | Feature            | Description                         | Priority |
| ---- | ------------------ | ----------------------------------- | -------- |
| A010 | Quick Add          | Global shortcut to add task         | P0       |
| A011 | Quick Timer        | Global shortcut to start/stop timer | P1       |
| A012 | Command Palette    | Cmd+K / Ctrl+K navigation           | P2       |
| A013 | Keyboard Shortcuts | Comprehensive shortcuts             | P1       |

#### 6.3 Automation Rules

| ID   | Feature             | Description                   | Priority |
| ---- | ------------------- | ----------------------------- | -------- |
| A020 | Auto-assign Project | Based on keywords or patterns | P3       |
| A021 | Auto-add Labels     | Based on task content         | P3       |
| A022 | Auto-set Priority   | Based on keywords             | P3       |
| A023 | Auto-schedule       | Suggest due dates             | P3       |
| A024 | Workflow Automation | If-this-then-that rules       | P3       |

#### 6.4 AI Features (Optional Plugin)

| ID   | Feature               | Description                  | Priority |
| ---- | --------------------- | ---------------------------- | -------- |
| A030 | Task Suggestions      | AI-suggested task breakdowns | P4       |
| A031 | Time Estimates        | AI-predicted task duration   | P4       |
| A032 | Priority Suggestions  | AI-recommended priorities    | P4       |
| A033 | Schedule Optimization | AI-optimized scheduling      | P4       |
| A034 | Smart Reminders       | AI-timed reminders           | P4       |

---

### 7. Reporting & Analytics

#### 7.1 Time Reports

| ID   | Feature           | Description                           | Priority |
| ---- | ----------------- | ------------------------------------- | -------- |
| R001 | Summary Report    | Total time by project/task/label/user | P0       |
| R002 | Detailed Report   | List of individual time entries       | P0       |
| R003 | Daily Report      | Time breakdown by day                 | P1       |
| R004 | Weekly Report     | Time breakdown by week                | P1       |
| R005 | Monthly Report    | Time breakdown by month               | P1       |
| R006 | Custom Date Range | Select any start and end date         | P1       |
| R007 | Comparison Report | Compare two periods side-by-side      | P2       |

#### 7.2 Productivity Reports

| ID   | Feature               | Description                    | Priority |
| ---- | --------------------- | ------------------------------ | -------- |
| R010 | Tasks Completed       | Count and trend over time      | P1       |
| R011 | Productivity Trends   | Visual charts                  | P2       |
| R012 | Streak Tracking       | Consecutive days of completion | P2       |
| R013 | Goal Progress         | Progress toward time goals     | P2       |
| R014 | Workload Distribution | Time across projects           | P2       |

#### 7.3 Team Reports

| ID   | Feature           | Description                   | Priority |
| ---- | ----------------- | ----------------------------- | -------- |
| R020 | Team Time Summary | Aggregate time by team member | P2       |
| R021 | Team Activity     | Recent team actions           | P2       |
| R022 | Workload Report   | Hours per team member         | P2       |
| R023 | Project Progress  | Team progress on projects     | P2       |

#### 7.4 Report Features

| ID   | Feature              | Description                                | Priority |
| ---- | -------------------- | ------------------------------------------ | -------- |
| R030 | Report Filtering     | Filter by project, task, user, date, label | P1       |
| R031 | Report Grouping      | Group by project, task, user, day, week    | P1       |
| R032 | Chart Visualizations | Bar, line, pie, donut charts               | P2       |
| R033 | Export CSV           | Download report data as CSV                | P1       |
| R034 | Export PDF           | Download formatted PDF report              | P2       |
| R035 | Saved Reports        | Save report configurations                 | P2       |
| R036 | Scheduled Reports    | Auto-generate on schedule                  | P3       |
| R037 | Report Sharing       | Share report via link                      | P2       |

---

### 8. Integrations

#### 8.1 Calendar Integration

| ID   | Feature               | Description                    | Priority |
| ---- | --------------------- | ------------------------------ | -------- |
| I001 | Google Calendar Sync  | Two-way sync                   | P2       |
| I002 | Outlook Calendar Sync | Two-way sync                   | P2       |
| I003 | CalDAV Support        | Standard protocol              | P2       |
| I004 | iCal Feed             | Subscribe to tasks as calendar | P2       |
| I005 | Calendar → Time Entry | One-click track from event     | P2       |

#### 8.2 Communication Integration

| ID   | Feature             | Description                   | Priority |
| ---- | ------------------- | ----------------------------- | -------- |
| I010 | Slack Integration   | Notifications, slash commands | P3       |
| I011 | Discord Integration | Bot for notifications         | P3       |
| I012 | Email to Task       | Create tasks by email         | P2       |
| I013 | Email Notifications | Transactional emails          | P2       |

#### 8.3 Developer Tools Integration

| ID   | Feature            | Description              | Priority |
| ---- | ------------------ | ------------------------ | -------- |
| I020 | GitHub Integration | Link tasks to issues/PRs | P3       |
| I021 | GitLab Integration | Link tasks to issues/MRs | P3       |
| I022 | Jira Import/Sync   | Import issues            | P3       |
| I023 | VS Code Extension  | Timer and task panel     | P3       |

#### 8.4 API & Webhooks

| ID   | Feature            | Description                 | Priority |
| ---- | ------------------ | --------------------------- | -------- |
| I030 | REST API           | Full CRUD API via DRF       | P1       |
| I031 | API Authentication | Token auth, API keys        | P1       |
| I032 | Webhooks           | Outgoing HTTP callbacks     | P2       |
| I033 | GraphQL API        | Optional GraphQL endpoint   | P3       |
| I034 | Zapier/n8n Support | Automation platform support | P3       |

#### 8.5 Import/Export

| ID   | Feature             | Description               | Priority |
| ---- | ------------------- | ------------------------- | -------- |
| I040 | Import from Todoist | Migrate from Todoist      | P2       |
| I041 | Import from Toggl   | Migrate from Toggl        | P2       |
| I042 | Import from CSV     | Bulk import via CSV       | P2       |
| I043 | Export All Data     | Complete data export      | P1       |
| I044 | Backup & Restore    | Database backup utilities | P1       |

---

### 9. Platforms & Apps

#### 9.1 Web Application

| ID    | Feature               | Description                       | Priority |
| ----- | --------------------- | --------------------------------- | -------- |
| PL001 | Responsive Web App    | Works on all devices              | P0       |
| PL002 | PWA Support           | Installable progressive web app   | P1       |
| PL003 | Offline Mode          | Work offline, sync when connected | P1       |
| PL004 | Cross-browser Support | Chrome, Firefox, Safari, Edge     | P0       |

#### 9.2 Desktop Applications

| ID    | Feature               | Description                     | Priority |
| ----- | --------------------- | ------------------------------- | -------- |
| PL010 | Windows App           | Native-like desktop app (Tauri) | P2       |
| PL011 | macOS App             | Native-like desktop app (Tauri) | P2       |
| PL012 | Linux App             | AppImage/Flatpak/Snap (Tauri)   | P2       |
| PL013 | System Tray/Menu Bar  | Persistent icon with timer      | P2       |
| PL014 | Global Shortcuts      | System-wide keyboard shortcuts  | P2       |
| PL015 | Desktop Notifications | Native OS notifications         | P2       |
| PL016 | Auto-start            | Option to start with system     | P3       |
| PL017 | Idle Detection        | Detect system idle state        | P2       |

#### 9.3 Mobile Applications

| ID    | Feature            | Description              | Priority |
| ----- | ------------------ | ------------------------ | -------- |
| PL020 | iOS App            | PWA or native app        | P2       |
| PL021 | Android App        | PWA or native app        | P2       |
| PL022 | Mobile Widgets     | Home screen widgets      | P3       |
| PL023 | Apple Watch App    | Timer on wearable        | P4       |
| PL024 | Wear OS App        | Timer on wearable        | P4       |
| PL025 | Push Notifications | Mobile push via FCM/APNs | P2       |
| PL026 | Offline Mobile     | Full offline support     | P2       |

#### 9.4 Browser Extension

| ID    | Feature            | Description                 | Priority |
| ----- | ------------------ | --------------------------- | -------- |
| PL030 | Chrome Extension   | Timer, quick add            | P2       |
| PL031 | Firefox Extension  | Timer, quick add            | P2       |
| PL032 | Edge Extension     | Timer, quick add            | P3       |
| PL033 | Safari Extension   | Timer, quick add            | P3       |
| PL034 | Site Timer Buttons | Inject buttons into sites   | P2       |
| PL035 | Page Context       | Auto-fill from current page | P3       |

---

### 10. Settings & Customization

#### 10.1 User Preferences

| ID   | Feature               | Description                        | Priority |
| ---- | --------------------- | ---------------------------------- | -------- |
| S001 | Language              | Multi-language support (i18n)      | P2       |
| S002 | Timezone              | User timezone setting              | P0       |
| S003 | Date Format           | DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD | P1       |
| S004 | Time Format           | 12-hour vs 24-hour                 | P1       |
| S005 | First Day of Week     | Sunday, Monday, Saturday           | P1       |
| S006 | Default Reminder Time | Default for new reminders          | P1       |
| S007 | Default Task Duration | Default estimate                   | P2       |

#### 10.2 Appearance

| ID   | Feature          | Description                | Priority |
| ---- | ---------------- | -------------------------- | -------- |
| S010 | Theme Selection  | Light, Dark, System (auto) | P0       |
| S011 | Custom Themes    | User-created color themes  | P3       |
| S012 | Accent Color     | Customizable primary color | P2       |
| S013 | Compact Mode     | Denser UI                  | P2       |
| S014 | Font Size        | Small, Medium, Large       | P2       |
| S015 | Sidebar Position | Left or right sidebar      | P2       |

#### 10.3 Notification Settings

| ID   | Feature                | Description                 | Priority |
| ---- | ---------------------- | --------------------------- | -------- |
| S020 | Reminder Notifications | Enable/disable reminders    | P1       |
| S021 | Email Preferences      | Which events trigger emails | P2       |
| S022 | Push Preferences       | Which events trigger push   | P2       |
| S023 | Quiet Hours            | Do not disturb schedule     | P2       |
| S024 | Sound Settings         | Notification sounds         | P2       |

#### 10.4 Data & Privacy

| ID   | Feature                   | Description                | Priority |
| ---- | ------------------------- | -------------------------- | -------- |
| S030 | Data Export               | Export all user data       | P1       |
| S031 | Account Deletion          | Permanently delete account | P1       |
| S032 | Activity Tracking Opt-out | Disable analytics          | P1       |
| S033 | Clear Local Data          | Remove cached data         | P1       |

---

## Phased Implementation Plan

### Phase 1: Foundation (MVP)

**Goal**: Core task management and time tracking  
**Duration**: 10-14 weeks

#### Infrastructure

- [ ] Django project structure
- [ ] PostgreSQL + Redis setup
- [ ] User auth (django-allauth)
- [ ] Tailwind CSS + HTMX + Alpine.js
- [ ] Docker Compose
- [ ] CI/CD pipeline

#### Features

- [ ] Task CRUD (T001-T007, T030-T033)
- [ ] Project CRUD (P001-P004, P012)
- [ ] Time tracking (TT001-TT002, TT004-TT006, TT008, TT010-TT014)
- [ ] Views (V001, V010-V012, V020, V024, V030, V040-V041)
- [ ] Reports (R001-R002, R006, R030-R031, R033)
- [ ] Settings (S002-S005, S010, C001-C004)

---

### Phase 2: Enhanced Experience (8-10 weeks)

- [ ] Subtasks, comments, checklists (T008-T010, T014)
- [ ] Recurring tasks, reminders (T020-T024, T026-T027)
- [ ] Bulk operations, archive (T034-T036)
- [ ] Board view, filters (V002, V013-V016, V031-V033, V043-V044)
- [ ] Timesheet view, goals (V021, TT040-TT043)
- [ ] NLP parsing (A001-A006, A010-A011, A013)
- [ ] Enhanced reports (R003-R005, R010-R013, R032)
- [ ] PWA, offline mode (PL002-PL003)
- [ ] Notifications (C030, C034-C035)

---

### Phase 3: Collaboration & Multi-Platform (10-12 weeks)

- [ ] Workspaces, teams (C010-C016, C020-C022)
- [ ] Activity feed, mentions (C031-C033, C036)
- [ ] Calendar view, table view (V003, V005, V022-V023)
- [ ] Calendar integrations (I001-I002, I004)
- [ ] REST API, webhooks (I030-I032)
- [ ] Import/export tools (I040-I044)
- [ ] Desktop app (PL010-PL015, PL017)
- [ ] Browser extension (PL030-PL031, PL034)
- [ ] Django Channels for real-time

---

### Phase 4: Advanced Features (8-10 weeks)

- [ ] File attachments, templates (T011-T012)
- [ ] Task dependencies (T013)
- [ ] Pomodoro timer (TT030-TT034)
- [ ] Timeline/Gantt view (V004)
- [ ] Automation rules (A020-A024)
- [ ] Advanced reports (R007, R034-R037)
- [ ] Third-party integrations (I010-I011, I020-I022)
- [ ] Mobile apps (PL020-PL022, PL025-PL026)
- [ ] Customization (S001, S011-S015, S020-S024)

---

### Phase 5: Enterprise & Scale (Ongoing)

- [ ] OAuth, 2FA, SSO/SAML (C005-C006)
- [ ] Audit logging, row-level security
- [ ] API rate limiting
- [ ] Performance optimization
- [ ] API Gateway integration guide
- [ ] AI plugin architecture (A030-A034)
- [ ] Plugin/extension system
- [ ] Theme marketplace

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                     │
├─────────────┬─────────────┬─────────────┬─────────────┬────────────────┤
│   Web App   │ Desktop App │   Mobile    │  Browser    │   Third-party  │
│(Django+HTMX)│   (Tauri)   │    (PWA)    │  Extension  │   (REST API)   │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴───────┬────────┘
       │             │             │             │              │
       └─────────────┴─────────────┴─────────────┴──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │     [Optional] API Gateway   │
                    │     (Kong / Traefik / nginx) │
                    └──────────────┬──────────────┘
                                   │
       ┌───────────────────────────┼───────────────────────────┐
       │                           │                           │
┌──────▼──────┐          ┌─────────▼─────────┐         ┌───────▼───────┐
│   Django    │          │  Django Channels  │         │    Celery     │
│  (Web+API)  │          │   (WebSocket)     │         │   (Workers)   │
│  Gunicorn   │          │     Daphne        │         │               │
└──────┬──────┘          └─────────┬─────────┘         └───────┬───────┘
       │                           │                           │
       └───────────────────────────┼───────────────────────────┘
                                   │
       ┌───────────────────────────┼───────────────────────────┐
       │                           │                           │
┌──────▼──────┐          ┌─────────▼─────────┐         ┌───────▼───────┐
│ PostgreSQL  │          │      Redis        │         │ File Storage  │
│  (Database) │          │  (Cache/Broker)   │         │ (Local/S3)    │
└─────────────┘          └───────────────────┘         └───────────────┘
```

---

## Frontend Architecture

### HTMX + Django Integration

```html
<!-- HTMX-enhanced form (no page reload) -->
<form
  hx-post="/tasks/create/"
  hx-target="#task-list"
  hx-swap="afterbegin"
  hx-on::after-request="this.reset()"
>
  {% csrf_token %}
  <input name="title" required />
  <button type="submit">Add Task</button>
</form>

<!-- Inline editing -->
<span
  hx-get="/tasks/{{ task.id }}/edit/"
  hx-trigger="click"
  hx-swap="outerHTML"
>
  {{ task.title }}
</span>

<!-- Live search -->
<input
  type="search"
  name="q"
  hx-get="/tasks/search/"
  hx-trigger="keyup changed delay:300ms"
  hx-target="#search-results"
/>

<!-- Real-time timer -->
<div
  id="timer-display"
  hx-get="/timer/current/"
  hx-trigger="every 1s"
  hx-swap="innerHTML"
>
  00:00:00
</div>
```

### Alpine.js for UI State

```html
<!-- Dropdown -->
<div x-data="{ open: false }" class="relative">
  <button @click="open = !open">Menu</button>
  <div x-show="open" @click.away="open = false" x-transition>
    <a href="#">Option 1</a>
  </div>
</div>

<!-- Dark mode toggle -->
<div
  x-data="{ dark: localStorage.getItem('theme') === 'dark' }"
  x-init="$watch('dark', val => { 
         localStorage.setItem('theme', val ? 'dark' : 'light');
         document.documentElement.classList.toggle('dark', val);
     })"
>
  <button @click="dark = !dark">
    <span x-show="!dark">🌙</span>
    <span x-show="dark">☀️</span>
  </button>
</div>
```

### Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  content: ["./templates/**/*.html", "./apps/**/templates/**/*.html"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: { 500: "#0ea5e9", 600: "#0284c7", 700: "#0369a1" },
        priority: { 1: "#ef4444", 2: "#f97316", 3: "#eab308", 4: "#6b7280" },
      },
    },
  },
  plugins: [require("@tailwindcss/forms"), require("@tailwindcss/typography")],
};
```

---

## Key Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.11"
django = "^5.0"
djangorestframework = "^3.15"
django-allauth = "^0.61"
psycopg = {extras = ["binary"], version = "^3.1"}
django-redis = "^5.4"
celery = {extras = ["redis"], version = "^5.3"}
django-celery-beat = "^2.5"
channels = {extras = ["daphne"], version = "^4.0"}
channels-redis = "^4.2"
django-tailwind = "^3.8"
django-htmx = "^1.17"
dateparser = "^1.2"
weasyprint = "^61.0"
gunicorn = "^21.2"
whitenoise = "^6.6"
```

---

## Deployment

### Docker Quick Start

```bash
git clone https://github.com/yourorg/workstate.git
cd workstate
cp .env.example .env
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py tailwind build
docker-compose exec web python manage.py createsuperuser
```

---

## License

```
Copyright 2024 Workstate Contributors
Licensed under the Apache License, Version 2.0
```

---

_Document Version: 3.0 | Last Updated: December 2024_
