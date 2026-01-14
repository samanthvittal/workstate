# Tech Stack

Complete technical stack documentation for Workstate.

## Backend Stack

### Core Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.11+ | Primary backend language with modern features, type hints, and strong ecosystem |
| **Framework** | Django | 5.x | Full-featured web framework with batteries-included philosophy, excellent ORM, and robust admin |
| **API Framework** | Django REST Framework | 3.15+ | RESTful API for mobile/desktop apps and third-party integrations |
| **Database** | PostgreSQL | 15+ | Primary data store with JSONB support, full-text search, and robust transaction support |
| **Cache/Session Store** | Redis | 7+ | Session storage, caching layer, and Celery message broker |
| **Task Queue** | Celery | 5.x | Background job processing for async tasks, scheduled jobs, and long-running operations |
| **Real-time** | Django Channels | 4.x | WebSocket support for live timer updates, notifications, and collaborative features |
| **ASGI Server** | Daphne | 4.x | ASGI server for Django Channels WebSocket connections |
| **WSGI Server** | Gunicorn | 21.x | Production WSGI server for Django HTTP requests |

### Backend Features & Libraries

| Purpose | Technology | Usage |
|---------|-----------|-------|
| **Authentication** | django-allauth | User registration, login, OAuth providers |
| **Task Scheduling** | django-celery-beat | Periodic task scheduling (reminders, reports, cleanup) |
| **Date Parsing** | dateparser | Natural language date/time parsing for task input |
| **PDF Generation** | weasyprint | Generate PDF reports from HTML templates |
| **PostgreSQL Adapter** | psycopg | PostgreSQL database adapter with binary support |
| **Redis Integration** | django-redis | Redis cache backend and session storage |
| **Channels Redis** | channels-redis | Redis channel layer for Django Channels |
| **Static Files** | whitenoise | Efficient static file serving in production |
| **HTMX Integration** | django-htmx | Server-side HTMX request detection and utilities |

## Frontend Stack

### Core Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Templating** | Django Templates | Built-in | Server-side HTML rendering with template inheritance |
| **Dynamic UX** | HTMX | 1.9+ | Dynamic page updates without full page reloads or heavy JavaScript |
| **Client-side Logic** | Alpine.js | 3.x | Lightweight reactivity for dropdowns, modals, and UI state |
| **CSS Framework** | Tailwind CSS | 3.x | Utility-first CSS framework for custom, responsive designs |
| **Tailwind Integration** | django-tailwind | 3.x | Tailwind CSS integration and build tooling for Django |
| **Icon Library** | Heroicons / Lucide | Latest | SVG icon sets optimized for Tailwind CSS |
| **Charts** | Chart.js | 4.x | Lightweight charting library for reports and analytics |

### Frontend Rationale

**Why HTMX over React/Vue:**
- Keeps development in Python/Django without requiring separate frontend framework
- Dramatically reduced JavaScript complexity and bundle size (~14KB vs 100KB+)
- Native server-side rendering eliminates SSR complexity
- Lower learning curve for Django developers
- Better SEO out of the box

**Why Tailwind over Bootstrap:**
- Smaller production builds (~10-20KB purged vs 150KB+)
- More flexibility for custom designs without fighting framework defaults
- Modern utility-first approach aligns well with HTMX and Django templates
- Excellent Django integration via django-tailwind
- Growing ecosystem and active development

**Why Alpine.js:**
- Minimal JavaScript for UI interactions (dropdowns, modals, toggles)
- Declarative syntax that feels natural in HTML templates
- Complements HTMX perfectly without overlapping concerns
- Tiny footprint and no build step required

## Database & Storage

### Primary Database

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Relational DB** | PostgreSQL 15+ | All application data (users, tasks, projects, time entries) |
| **Full-Text Search** | PostgreSQL FTS | Built-in full-text search for tasks and projects |
| **JSONB Storage** | PostgreSQL JSONB | Flexible storage for metadata, settings, and extension data |

### Caching & Sessions

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Cache Backend** | Redis 7+ | Page caching, query result caching, session storage |
| **Message Broker** | Redis 7+ | Celery message broker for task queue |
| **Channel Layer** | Redis 7+ | Django Channels message passing for WebSocket |

### File Storage

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Local Storage** | Filesystem | Default file upload storage for self-hosted deployments |
| **Cloud Storage** | S3-compatible | Optional S3/MinIO/B2 for file attachments (future) |

## Testing & Quality

### Testing Framework

| Tool | Purpose |
|------|---------|
| **pytest** | Primary test framework with Django plugin |
| **pytest-django** | Django-specific test utilities and fixtures |
| **pytest-cov** | Code coverage reporting |
| **factory-boy** | Test data factories for clean test setup |

### Code Quality

| Tool | Purpose |
|------|---------|
| **ruff** | Fast Python linter and formatter (replaces flake8, black, isort) |
| **bandit** | Security vulnerability scanner for Python code |
| **mypy** | Static type checking for Python type hints |
| **pre-commit** | Git hooks for automated quality checks |

## Deployment & Infrastructure

### Containerization

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Container Runtime** | Docker | Application containerization |
| **Orchestration** | Docker Compose | Local and small-scale deployment orchestration |
| **Production Option** | Kubernetes | Optional for larger-scale deployments |

### CI/CD

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **CI Platform** | GitHub Actions | Automated testing, linting, and deployment |
| **Container Registry** | GitHub Container Registry | Docker image storage and distribution |

### Hosting

| Deployment Type | Technology | Use Case |
|-----------------|-----------|----------|
| **Self-Hosted (Primary)** | Docker + Docker Compose | Default deployment model |
| **VPS/Cloud** | DigitalOcean, Linode, Hetzner | Single-server deployments |
| **Enterprise** | Kubernetes + Helm | High-availability multi-instance |

### Monitoring (Optional)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Error Tracking** | Sentry | Production error monitoring and alerting |
| **Metrics** | Prometheus + Grafana | System metrics and performance monitoring |
| **Logging** | ELK Stack / Loki | Centralized log aggregation and search |

## Multi-Platform Support

### Desktop Applications

| Platform | Technology | Description |
|----------|-----------|-------------|
| **Windows** | Tauri | Lightweight desktop app using Rust + WebView |
| **macOS** | Tauri | Native-like app with system tray and shortcuts |
| **Linux** | Tauri | AppImage/Flatpak/Snap packages |

**Why Tauri:**
- Smaller bundle size than Electron (~600KB vs 50MB+)
- Better performance and resource usage
- Reuses web frontend code
- Native system integration

### Mobile Applications

| Platform | Technology | Description |
|----------|-----------|-------------|
| **iOS** | PWA (Primary) | Progressive Web App installable from Safari |
| **Android** | PWA (Primary) | Progressive Web App installable from Chrome |
| **Native (Future)** | Python (Kivy/BeeWare) | Optional native apps if PWA limitations emerge |

**PWA Advantages:**
- Single codebase shared with web app
- Offline support via Service Workers
- Push notifications
- No app store approval process
- Instant updates

### Browser Extensions

| Browser | Technology | Features |
|---------|-----------|----------|
| **Chrome** | Web Extension API | Quick task add, timer control |
| **Firefox** | Web Extension API | Quick task add, timer control |
| **Edge** | Web Extension API | Quick task add, timer control |
| **Safari** | Web Extension API | Quick task add, timer control (future) |

## API & Integration

### API Technology

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **REST API** | Django REST Framework | Primary API for all clients |
| **API Authentication** | Token Auth + API Keys | Secure API access for integrations |
| **API Documentation** | drf-spectacular | Auto-generated OpenAPI/Swagger docs |
| **Webhooks** | Django Signals | Outgoing HTTP callbacks for events |
| **GraphQL (Future)** | Graphene-Django | Optional GraphQL endpoint |

### External Integrations

| Service | Purpose | Implementation |
|---------|---------|----------------|
| **Google Calendar** | Two-way sync | OAuth2 + Google Calendar API |
| **Outlook Calendar** | Two-way sync | OAuth2 + Microsoft Graph API |
| **GitHub** | Issue linking | OAuth2 + GitHub API |
| **GitLab** | Issue linking | OAuth2 + GitLab API |
| **Slack** | Notifications | Webhook + Slack API |

## Development Tools

### Local Development

| Tool | Purpose |
|------|---------|
| **Poetry** | Python dependency management |
| **Docker Compose** | Local service orchestration |
| **django-debug-toolbar** | Django debugging and profiling |
| **Werkzeug** | Enhanced debugger |

### Version Control

| Tool | Purpose |
|------|---------|
| **Git** | Source code version control |
| **GitHub** | Repository hosting and collaboration |
| **pre-commit hooks** | Automated code quality checks |

## Security

### Authentication & Authorization

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Password Hashing** | Django (PBKDF2) | Secure password storage |
| **2FA (Future)** | django-otp | Two-factor authentication |
| **OAuth Providers** | django-allauth | Google, GitHub, GitLab login |
| **SSO/SAML (Future)** | python-saml | Enterprise SSO integration |

### Security Scanning

| Tool | Purpose |
|------|---------|
| **bandit** | Static security analysis |
| **safety** | Dependency vulnerability scanning |
| **OWASP ZAP** | Web application security testing |

## Environment Variables

Key configuration managed via environment variables:

```bash
# Django
SECRET_KEY=<django-secret>
DEBUG=False
ALLOWED_HOSTS=workstate.example.com

# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/workstate

# Redis
REDIS_URL=redis://redis:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Storage (optional)
AWS_ACCESS_KEY_ID=<s3-key>
AWS_SECRET_ACCESS_KEY=<s3-secret>
AWS_STORAGE_BUCKET_NAME=workstate-files
```

## Production Stack Summary

Minimal production deployment:
```yaml
services:
  web:           # Django + Gunicorn (WSGI)
  channels:      # Daphne (ASGI/WebSocket)
  celery:        # Background worker
  celery-beat:   # Scheduled tasks
  postgres:      # Database
  redis:         # Cache/broker/channels
  nginx:         # Reverse proxy (optional)
```

This stack provides:
- Modern Python/Django foundation
- Dynamic UX without heavy JavaScript
- Self-hosted deployment flexibility
- Multi-platform support (web, desktop, mobile)
- Extensible API for integrations
- Production-ready monitoring and security
