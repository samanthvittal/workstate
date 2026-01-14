# Workstate Development Setup Instructions

## Prerequisites

- Python 3.12+ installed
- pip package manager
- Git

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd workstate
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and update any necessary values. For development, the defaults should work fine.

### 5. Run Database Migrations

```bash
python manage.py migrate
```

This will create the SQLite database and apply all migrations, including:
- Django's default tables (auth, sessions, etc.)
- UserProfile table from Task Group 1

### 6. Create a Superuser (Admin)

```bash
python manage.py createsuperuser
```

Follow the prompts to create your first admin user. You'll need:
- Email address (used as username)
- Password (minimum 8 characters)

The UserProfile will be automatically created via signal handlers.

### 7. Run the Development Server

```bash
python manage.py runserver
```

The application will be available at: http://localhost:8000

The Django admin interface will be available at: http://localhost:8000/admin

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest accounts/tests/test_models.py
```

### Run with Verbose Output

```bash
pytest -v
```

### Using the Test Runner Script

```bash
chmod +x run_tests.sh
./run_tests.sh
```

## Project Structure

```
workstate/
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── pytest.ini            # Pytest configuration
├── .env.example          # Environment variables template
├── .env                  # Your local environment variables (not in git)
├── db.sqlite3            # SQLite database (created after migration)
├── media/                # User-uploaded files (avatars, etc.)
├── workstate/            # Main project settings
│   ├── settings.py       # Django settings
│   ├── urls.py          # Root URL configuration
│   └── wsgi.py          # WSGI application
└── accounts/             # User authentication app
    ├── models.py         # UserProfile model
    ├── admin.py         # Django admin configuration
    ├── signals.py       # Signal handlers
    ├── migrations/      # Database migrations
    └── tests/           # Test files
```

## Verifying Your Setup

After completing the setup, verify everything works:

1. **Check migrations:**
   ```bash
   python manage.py showmigrations
   ```
   You should see all migrations marked with [X]

2. **Run tests:**
   ```bash
   pytest accounts/tests/test_models.py -v
   ```
   All 8 tests should pass

3. **Access admin interface:**
   - Navigate to http://localhost:8000/admin
   - Login with your superuser credentials
   - You should see Users and User Profiles in the admin

4. **Check your user profile:**
   - In the admin, click on "Users"
   - Click on your user
   - You should see the Profile section with fields like timezone, full_name, etc.

## Common Issues

### ImportError: No module named 'django'

Make sure you've activated the virtual environment:
```bash
source venv/bin/activate
```

### Migration errors

If you get migration errors, try:
```bash
python manage.py migrate --run-syncdb
```

### Permission errors on run_tests.sh

Make the script executable:
```bash
chmod +x run_tests.sh
```

## Next Steps

Now that Task Group 1 is complete, you can proceed with:
- Task Group 2: Workspace Models
- Task Group 3: User Preferences and Security Models

## Development Workflow

1. Always activate the virtual environment before working
2. Create migrations after model changes: `python manage.py makemigrations`
3. Apply migrations: `python manage.py migrate`
4. Run tests before committing: `pytest`
5. Follow the project coding standards in `agent-os/standards/`

## Environment Variables Reference

Key environment variables in `.env`:

- `SECRET_KEY`: Django secret key (change in production!)
- `DEBUG`: Set to True for development, False for production
- `DATABASE_URL`: Database connection string
- `EMAIL_BACKEND`: Email backend (console for dev, SMTP for prod)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

## Media Files

User-uploaded files (like avatars) are stored in:
- **Development:** `media/` directory in project root
- **Production:** Configure cloud storage (S3-compatible)

Make sure the `media/` directory has proper write permissions:
```bash
mkdir -p media/avatars
chmod 755 media
```

## Database

### Development (SQLite)
- Database file: `db.sqlite3`
- Automatically created on first migration
- Good for development, not recommended for production

### Production (PostgreSQL)
- Update `DATABASE_URL` in `.env` with PostgreSQL connection string
- Install psycopg2-binary: Already in requirements.txt
- Example: `DATABASE_URL=postgresql://user:password@localhost:5432/workstate`

## Additional Resources

- Django Documentation: https://docs.djangoproject.com/
- Pytest-Django Documentation: https://pytest-django.readthedocs.io/
- Project Standards: See `agent-os/standards/` directory
- Task Breakdown: See `agent-os/specs/2026-01-02-user-authentication-workspace-setup/tasks.md`
