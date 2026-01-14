# Workstate Development Setup Guide

This guide walks you through setting up the Workstate application for local development.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git
- PostgreSQL 15+ (installed and running locally)

## Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd workstate
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the project root directory. Use the `.env.example` file as a template:

```bash
cp .env.example .env
```

#### Required Environment Variables

The following environment variables are needed for development:

**Django Settings:**
- `SECRET_KEY`: Django secret key for cryptographic signing (change in production)
- `DEBUG`: Set to `True` for development, `False` for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed host/domain names

**Database Settings:**
- `DB_NAME`: PostgreSQL database name (default: `workstate`)
- `DB_USER`: PostgreSQL username (default: `workstateadmin`)
- `DB_PASSWORD`: PostgreSQL password (default: `admin123`)
- `DB_HOST`: PostgreSQL host (default: `localhost`)
- `DB_PORT`: PostgreSQL port (default: `5432`)

**Email Settings:**
- `EMAIL_BACKEND`: Email backend to use for sending emails
  - Development: `django.core.mail.backends.console.EmailBackend`
  - Production: `django.core.mail.backends.smtp.EmailBackend`

**Email Configuration (if using SMTP in production):**
- `EMAIL_HOST`: SMTP server hostname
- `EMAIL_PORT`: SMTP server port (usually 587 for TLS)
- `EMAIL_HOST_USER`: SMTP username
- `EMAIL_HOST_PASSWORD`: SMTP password
- `EMAIL_USE_TLS`: Set to `True` to use TLS encryption
- `DEFAULT_FROM_EMAIL`: Default email address for outgoing emails

#### Example Development `.env` File

See `.env.example` for a complete example configuration.

### 5. PostgreSQL Database Setup

#### Create Database and User

First, ensure PostgreSQL is running locally. Then create the database and user:

```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Create database and user
CREATE DATABASE workstate;
CREATE USER workstateadmin WITH PASSWORD 'admin123';
GRANT ALL PRIVILEGES ON DATABASE workstate TO workstateadmin;

# Grant schema privileges (PostgreSQL 15+)
\c workstate
GRANT ALL ON SCHEMA public TO workstateadmin;

# Exit psql
\q
```

**Note:** The default credentials are:
- Database: `workstate`
- Username: `workstateadmin`
- Password: `admin123`

These credentials are configured in `.env` and can be changed if needed.

#### Verify Database Connection

Test the database connection:

```bash
psql -U workstateadmin -d workstate -h localhost
```

If successful, you should see the PostgreSQL prompt. Type `\q` to exit.

### 6. Run Database Migrations

Apply all database migrations to create the necessary tables:

```bash
python manage.py migrate
```

This will run migrations in the following order:
1. Django built-in migrations (auth, sessions, contenttypes, etc.)
2. django-allauth migrations (account, socialaccount)
3. Accounts app migrations (user profiles, workspaces, preferences, login attempts)

#### Expected Migrations

The accounts app includes the following migrations:
- `0001_initial.py`: Creates UserProfile, UserPreference, and LoginAttempt models
- `0002_add_workspace_model.py`: Creates Workspace model

### 7. Create Initial Superuser

Create an admin user to access the Django admin and admin dashboard:

```bash
python manage.py createsuperuser
```

You will be prompted to enter:
- Email address (used for login)
- Password (minimum 8 characters)

Note: The createsuperuser command will automatically:
- Create a User account with admin privileges (is_staff=True, is_superuser=True)
- Create associated UserProfile with default values
- Create UserPreference with default timezone (UTC) and format settings
- Create a personal Workspace with a random constellation name

### 8. Media File Storage Configuration

User-uploaded files (avatars) are stored in the `media/` directory.

**Development:**
- Media files are served by Django's development server
- Location: `<project_root>/media/`
- URL path: `/media/`

**Production:**
- Configure your web server (nginx, Apache) to serve media files directly
- Set appropriate file permissions for the media directory
- Consider using cloud storage (S3, CloudFront) for scalability

#### Media Directory Structure

```
media/
└── avatars/          # User profile avatar images
    └── user_<id>/    # Organized by user ID
```

Ensure the media directory has proper write permissions:

```bash
mkdir -p media/avatars
chmod 755 media
```

### 9. Email Backend Configuration

**Development (Console Backend):**

Emails are printed to the console instead of being sent. This is configured by default in `.env.example`:

```
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

When you register a user or trigger a password reset, the email content will appear in your console/terminal.

**Testing Email Verification Flow:**

1. Register a new user
2. Check the console for the verification email
3. Copy the verification URL from the console output
4. Open the URL in your browser to verify the email

**Production (SMTP Backend):**

For production, configure an SMTP server:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@workstate.com
```

### 10. Static Files

Collect static files for production deployment:

```bash
python manage.py collectstatic
```

In development, static files are served automatically by Django.

### 11. Run the Development Server

Start the Django development server:

```bash
python manage.py runserver
```

The application will be available at: http://127.0.0.1:8000/

## Testing the Setup

### Verify Database Migrations

Check that all migrations have been applied:

```bash
python manage.py showmigrations
```

All migrations should have an `[X]` mark indicating they've been applied.

### Verify Email Backend

Register a test user and check that the verification email appears in the console.

### Verify Media Uploads

1. Log in with your superuser account
2. Navigate to the profile page
3. Upload an avatar image
4. Verify the file is saved to `media/avatars/user_<id>/`

### Verify Timezone Middleware

The timezone middleware should automatically activate the user's timezone for all datetime displays.

Check that:
1. User preferences include timezone selection
2. Datetime values are displayed in the user's selected timezone
3. Database values are stored in UTC

## Common Issues

### Migration Errors

If you encounter migration errors, try:

```bash
python manage.py migrate --run-syncdb
```

### Media Upload Permissions

If avatar uploads fail, check directory permissions:

```bash
chmod -R 755 media/
```

### Email Verification Not Working

Ensure:
1. `EMAIL_BACKEND` is set to console backend in development
2. `ACCOUNT_EMAIL_VERIFICATION` is set to `mandatory` in settings
3. Check console output for verification URLs

## Next Steps

After setup is complete:

1. Review the [Admin User Setup Guide](ADMIN_SETUP.md)
2. Review the [Constellation Name Generator Documentation](CONSTELLATION_NAMES.md)
3. Review the [Migration Checklist](MIGRATION_CHECKLIST.md)
4. Read the [Security Configuration Guide](SECURITY_CHECKLIST.md)

## Development Workflow

### Running Tests

Run the test suite to verify everything works:

```bash
pytest
```

Run specific test files:

```bash
pytest accounts/tests/test_models.py
```

### Database Reset

To reset the database during development:

```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Code Formatting

The project uses ruff for linting and formatting:

```bash
ruff check .
ruff format .
```

## Support

For issues or questions:
- Check the documentation in the `docs/` directory
- Review the project README.md
- Check the issue tracker
