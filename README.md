# Workstate
**Where tasks meet time**

Workstate is a self-hosted, open-source application that combines task management and time tracking into a single, coherent workflow.
It treats *tasks* and *time* as first-class citizens, helping you understand not just what you work on—but how long it actually takes.

---

## ✨ Philosophy

Most productivity tools focus either on *what* you do or *how long* you do it.
Workstate is built on the idea that these two are inseparable.

- Tasks represent **intent**
- Time represents **reality**
- Insight comes from connecting the two

Workstate is designed to be:
- **Self-hosted first**
- **Privacy-respecting**
- **Minimal, but extensible**
- **Friendly to developers and non-developers alike**

---

## 🌱 Why Workstate?

Because understanding your work requires understanding both **intent** and **time**.

---

## 🎯 Goals

- Unified task and time tracking
- Clear, explicit data model (no magic automation)
- Self-hosted by default
- Works well for individuals and small teams
- Open source and permissively licensed
- Easy to extend via APIs and integrations

---

## 🚫 Non-Goals

To keep the project focused and sustainable, Workstate intentionally does **not** aim to:

- Be a clone of any existing proprietary product
- Replicate proprietary UX, workflows, or APIs
- Offer built-in SaaS hosting (at least initially)
- Track users, collect analytics, or monetize data
- Compete on marketing-driven feature bloat
- Reimplementing proprietary features based on reverse engineering

Workstate values **clarity over cleverness** and **control over convenience**.

---

## 🏗️ Project Status

🚧 Early development

The initial focus is on:
- Core domain models (tasks, states, time sessions)
- A clean and well-documented API
- A solid foundation for future web and mobile clients

Details will evolve as development progresses.

---

## ✨ Features

### User Authentication & Security

Workstate provides a secure, self-hosted authentication system designed for privacy and control:

**Registration & Email Verification**
- Secure email/password registration with PBKDF2 password hashing
- Mandatory email verification before account activation
- Automatic duplicate email detection with helpful redirection
- Minimum 8-character password requirement

**Automatic Workspace Creation**
- Every user gets a personal workspace automatically created upon registration
- Custom workspace names can be specified during signup
- Random constellation names assigned as delightful defaults (Orion, Andromeda, Cassiopeia, etc.)
- Workspace names can be changed after account creation

**Secure Login with Account Protection**
- Email/password authentication
- "Remember Me" option for extended sessions (30 days vs 2 weeks)
- Account lockout after 3 consecutive failed login attempts
- Automatic unlock after 30-minute cooldown period
- Clear lockout messaging with wait time

**Password Management**
- Self-service password reset flow via email
- Secure token-based reset links
- Password strength validation on reset

**User Profile Management**
- Customizable profiles with avatar upload
- Support for job title, company, and contact information
- Profile picture with file type and size validation
- All profile changes saved with single action

### Timezone & Preferences

Workstate ensures accurate time tracking across global teams:

**Timezone Support**
- Automatic timezone detection from browser settings
- Manual timezone override available
- All dates and times displayed in user's selected timezone
- Database stores times in UTC for consistency

**User Preferences**
- Date format selection (MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD)
- Time format selection (12-hour, 24-hour)
- Week start day preference (Sunday, Monday, Saturday)
- Preferences apply consistently across the entire application

### Admin Capabilities

Comprehensive user management tools for platform administrators:

**Admin Dashboard**
- Clean, user-friendly interface for user management
- Search users by name or email
- Filter by status (active, locked, unverified)
- Pagination for large user lists
- View detailed user profiles and preferences

**Admin Actions**
- Manually unlock locked user accounts (bypass 30-minute cooldown)
- Trigger password reset emails for users
- Delete user accounts with cascade deletion
- Grant or revoke admin privileges
- View user login history

**Security & Access Control**
- Permission checks prevent unauthorized access to admin features
- Admin-only routes protected with decorators
- Granular control over admin capabilities

---

## 📦 Self-Hosting

Workstate is designed to be run on infrastructure you control.

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd workstate

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to access the application.

### Documentation

Comprehensive setup and configuration documentation is available in the `/docs` directory:

- **[Setup Guide](docs/SETUP.md)**: Complete development environment setup instructions
- **[Admin Setup](docs/ADMIN_SETUP.md)**: Creating and managing admin users
- **[Constellation Names](docs/CONSTELLATION_NAMES.md)**: Workspace naming system documentation
- **[Migration Checklist](docs/MIGRATION_CHECKLIST.md)**: Database migration and deployment guide
- **[Security Checklist](docs/SECURITY_CHECKLIST.md)**: Security configuration verification

### Requirements

- Python 3.10 or higher
- pip (Python package manager)
- SQLite (development) or PostgreSQL (production recommended)

### Environment Configuration

Key environment variables (see `.env.example` for full list):

- `SECRET_KEY`: Django secret key for cryptographic signing
- `DEBUG`: Enable/disable debug mode
- `DATABASE_URL`: Database connection string
- `EMAIL_BACKEND`: Email backend for verification emails
- `ALLOWED_HOSTS`: Allowed hostnames for the application

Detailed configuration instructions are available in the [Setup Guide](docs/SETUP.md).

---

## 🔐 Security

Workstate implements industry-standard security practices:

- **Password Hashing**: PBKDF2 algorithm with automatic salting
- **CSRF Protection**: Enabled on all forms
- **Session Security**: Configurable session timeouts and secure cookies
- **File Upload Validation**: Type and size restrictions on avatars
- **Account Lockout**: Protection against brute-force attacks
- **Email Verification**: Prevents unauthorized account creation
- **Admin Access Controls**: Permission-based access to sensitive operations

For production deployments, see the [Security Checklist](docs/SECURITY_CHECKLIST.md) for additional hardening steps.

---

## 🛠️ Technology Stack

**Backend:**
- Django (Python web framework)
- django-allauth (email verification)
- PostgreSQL (production database)
- SQLite (development database)

**Frontend:**
- HTMX (dynamic interactions without heavy JavaScript)
- Alpine.js (client-side interactivity)
- Tailwind CSS (utility-first styling)

**Testing:**
- pytest (test framework)
- ruff (linting and formatting)

See the [Tech Stack Documentation](agent-os/standards/global/tech-stack.md) for complete details.

---

## 📄 License

Workstate is licensed under the **Apache License, Version 2.0**.

You are free to:
- Use the software for any purpose
- Modify and distribute it
- Use it commercially

See the `LICENSE` file for full details.

---

## ⚖️ Disclaimer

Workstate is an independent, open-source project and is **not affiliated with, endorsed by, or connected to** any third-party task or time-tracking products.

All product names, trademarks, and registered trademarks are the property of their respective owners.

---

## 🤝 Contributing

Contribution guidelines are available in [CONTRIBUTING.md](CONTRIBUTING.md).

We welcome:
- Bug reports and feature requests
- Documentation improvements
- Code contributions
- Design feedback

Please review the contributing guidelines before submitting pull requests.

---

## 📚 Documentation

- [Setup Guide](docs/SETUP.md) - Development environment setup
- [Admin Setup](docs/ADMIN_SETUP.md) - Admin user management
- [Constellation Names](docs/CONSTELLATION_NAMES.md) - Workspace naming system
- [Migration Checklist](docs/MIGRATION_CHECKLIST.md) - Deployment preparation
- [Security Checklist](docs/SECURITY_CHECKLIST.md) - Security configuration

---

## 🗺️ Roadmap

Current implementation status:

- ✅ User authentication with email verification
- ✅ Automatic workspace creation
- ✅ User profiles and preferences
- ✅ Timezone-aware datetime handling
- ✅ Admin user management dashboard
- 🚧 Task management (in development)
- 🚧 Time tracking (in development)
- 📅 Reporting and analytics (planned)
- 📅 Team workspaces (planned)
- 📅 API access (planned)

---

## 💬 Support

For questions, issues, or suggestions:
- Open an issue in the repository
- Check existing documentation in `/docs`
- Review the [Contributing Guide](CONTRIBUTING.md)

---

**Built with clarity, designed for control.**
