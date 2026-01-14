# Migration Checklist

This checklist guides you through database migrations and deployment preparation for the Workstate authentication feature.

## Overview

This checklist ensures that all database migrations are applied correctly, the initial admin user is created, email verification is working, media uploads are configured, and timezone middleware is functioning properly.

## Pre-Migration Checks

### 1. Backup Existing Database (Production Only)

Before running migrations in production, always create a backup:

**PostgreSQL:**
```bash
pg_dump -U username -d workstate > backup_$(date +%Y%m%d_%H%M%S).sql
```

**SQLite:**
```bash
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)
```

### 2. Verify Django Settings

Ensure your Django settings are correctly configured:

```bash
python manage.py check
```

Expected output: `System check identified no issues (0 silenced).`

### 3. Check Installed Apps

Verify all required apps are in `INSTALLED_APPS`:

**File:** `workstate/settings.py`

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third-party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # Local apps
    'accounts.apps.AccountsConfig',
]
```

## Migration Steps

### 1. Check Pending Migrations

View all pending migrations before applying:

```bash
python manage.py showmigrations
```

**Expected Output:**
```
accounts
 [ ] 0001_initial
 [ ] 0002_add_workspace_model
admin
 [X] 0001_initial
 [X] 0002_logentry_remove_auto_add
 [X] 0003_logentry_add_action_flag_choices
...
```

Unchecked boxes `[ ]` indicate pending migrations.

### 2. Run Migrations in Correct Order

Django automatically handles migration dependencies, but verify the order:

```bash
python manage.py migrate --plan
```

This shows the planned migration order without executing them.

### 3. Apply All Migrations

Run all pending migrations:

```bash
python manage.py migrate
```

**Expected Output:**
```
Operations to perform:
  Apply all migrations: accounts, admin, auth, contenttypes, sessions, sites, account, socialaccount
Running migrations:
  Applying accounts.0001_initial... OK
  Applying accounts.0002_add_workspace_model... OK
  ...
```

### 4. Verify Migration Success

Confirm all migrations were applied:

```bash
python manage.py showmigrations
```

All migrations should now show `[X]` (checked).

### 5. Verify Database Schema

Check that all expected tables exist:

**PostgreSQL:**
```bash
psql -U username -d workstate -c "\dt"
```

**SQLite:**
```bash
sqlite3 db.sqlite3 ".tables"
```

**Expected Tables:**
- `accounts_userprofile`
- `accounts_userpreference`
- `accounts_workspace`
- `accounts_loginattempt`
- `auth_user` (Django's built-in User model)
- `account_emailaddress` (django-allauth)
- `account_emailconfirmation` (django-allauth)
- Plus standard Django tables (sessions, admin, etc.)

## Initial Superuser Creation

### 1. Create Initial Superuser

Create the first admin user:

```bash
python manage.py createsuperuser
```

**Interactive Prompts:**
```
Email address: admin@workstate.com
Password:
Password (again):
Superuser created successfully.
```

### 2. Verify Superuser Creation

Verify the superuser and related models were created:

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from accounts.models import UserProfile, UserPreference, Workspace

User = get_user_model()

# Check user exists
admin = User.objects.get(email='admin@workstate.com')
print(f"User: {admin.email}")
print(f"Is staff: {admin.is_staff}")
print(f"Is superuser: {admin.is_superuser}")

# Check UserProfile exists
profile = UserProfile.objects.get(user=admin)
print(f"Profile created: {profile.created_at}")

# Check UserPreference exists
prefs = UserPreference.objects.get(user=admin)
print(f"Timezone: {prefs.timezone}")
print(f"Date format: {prefs.date_format}")

# Check Workspace exists
workspace = Workspace.objects.get(owner=admin)
print(f"Workspace: {workspace.name}")
print(f"Is personal: {workspace.is_personal}")
```

**Expected Output:**
```
User: admin@workstate.com
Is staff: True
Is superuser: True
Profile created: 2026-01-04 12:00:00+00:00
Timezone: UTC
Date format: MM/DD/YYYY
Workspace: Orion  # or another constellation name
Is personal: True
```

### 3. Test Superuser Login

Verify login works:

```bash
python manage.py runserver
```

Navigate to http://127.0.0.1:8000/admin/ and log in with your superuser credentials.

## Email Verification Testing

### 1. Verify Email Backend Configuration

Check that email backend is set for development:

**File:** `.env` or `workstate/settings.py`

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### 2. Test Email Verification Flow

**Register a Test User:**

1. Navigate to http://127.0.0.1:8000/accounts/register/
2. Fill in registration form:
   - Email: testuser@example.com
   - Password: TestPassword123
   - Full name: Test User
3. Submit the form

**Check Console Output:**

The verification email should appear in your console/terminal:

```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: [example.com] Please Confirm Your E-mail Address
From: webmaster@localhost
To: testuser@example.com
Date: Fri, 04 Jan 2026 12:00:00 -0000
Message-ID: <...>

Hello from example.com!

You're receiving this e-mail because user testuser@example.com has given yours as an e-mail address to connect their account.

To confirm this is correct, go to http://127.0.0.1:8000/accounts/confirm-email/ABC123...

Thank you for using example.com!
example.com
```

**Verify Email:**

1. Copy the verification URL from console
2. Open it in your browser
3. Click "Confirm"
4. Verify redirect to login page

**Check Database:**

```bash
python manage.py shell
```

```python
from allauth.account.models import EmailAddress

email = EmailAddress.objects.get(email='testuser@example.com')
print(f"Email: {email.email}")
print(f"Verified: {email.verified}")
print(f"Primary: {email.primary}")
```

**Expected Output:**
```
Email: testuser@example.com
Verified: True
Primary: True
```

### 3. Test Login After Verification

1. Navigate to http://127.0.0.1:8000/accounts/login/
2. Log in with testuser@example.com credentials
3. Verify successful login

## Media Upload Directory Verification

### 1. Check Media Directory Exists

Verify media directory structure:

```bash
ls -la media/
```

**Expected Output:**
```
drwxr-xr-x  3 user user 4096 Jan  4 12:00 .
drwxr-xr-x 10 user user 4096 Jan  4 12:00 ..
drwxr-xr-x  2 user user 4096 Jan  4 12:00 avatars
```

### 2. Create Media Directory (if missing)

If the media directory doesn't exist:

```bash
mkdir -p media/avatars
chmod 755 media
chmod 755 media/avatars
```

### 3. Verify Media Configuration

**File:** `workstate/settings.py`

```python
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### 4. Test Avatar Upload

**Upload Avatar:**

1. Log in to the application
2. Navigate to profile page: http://127.0.0.1:8000/profile/
3. Click "Choose File" for avatar
4. Select an image file (JPG, PNG, or GIF)
5. Click "Save Profile"

**Verify File Saved:**

```bash
ls -la media/avatars/
```

You should see uploaded avatar files organized by user ID.

**Check Database:**

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from accounts.models import UserProfile

User = get_user_model()
user = User.objects.get(email='testuser@example.com')
profile = UserProfile.objects.get(user=user)

print(f"Avatar path: {profile.avatar}")
print(f"Avatar URL: {profile.avatar.url if profile.avatar else 'No avatar'}")
```

### 5. Test Media Serving (Development)

Ensure media files are served in development:

**File:** `workstate/urls.py`

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... your URL patterns
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Access avatar URL in browser to verify file is served correctly.

## Timezone Middleware Testing

### 1. Verify Middleware Configuration

**File:** `workstate/settings.py`

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.TimezoneMiddleware',  # Custom timezone middleware
]
```

### 2. Test Timezone Activation

**Create Test Script:**

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from accounts.models import UserPreference
from django.utils import timezone
import pytz

User = get_user_model()

# Get test user
user = User.objects.get(email='testuser@example.com')

# Update timezone preference
prefs = UserPreference.objects.get(user=user)
prefs.timezone = 'America/New_York'
prefs.save()

print(f"User timezone set to: {prefs.timezone}")

# Check current timezone (should be UTC in shell)
print(f"Current timezone: {timezone.get_current_timezone()}")
```

### 3. Test Timezone in Views

1. Log in as testuser
2. Navigate to preferences page
3. Change timezone to different zone (e.g., America/New_York)
4. Save preferences
5. Navigate to any page displaying timestamps
6. Verify times are displayed in selected timezone

### 4. Verify Database Stores UTC

```bash
python manage.py shell
```

```python
from accounts.models import UserProfile
from django.utils import timezone

profile = UserProfile.objects.first()

# Check created_at timestamp
print(f"Created at (DB): {profile.created_at}")
print(f"Timezone: {profile.created_at.tzinfo}")

# Should show UTC
# Example: 2026-01-04 12:00:00+00:00
```

## Post-Migration Verification

### 1. Run Test Suite

Execute all tests to verify functionality:

```bash
pytest
```

**Expected:** All tests pass.

### 2. Check for Migration Conflicts

Ensure no conflicting migrations exist:

```bash
python manage.py makemigrations --check --dry-run
```

**Expected Output:**
```
No changes detected
```

### 3. Verify Static Files (Production)

Collect static files for production:

```bash
python manage.py collectstatic
```

Verify static files are collected to `staticfiles/` directory.

### 4. Security Check

Run Django's security check:

```bash
python manage.py check --deploy
```

Review any warnings (some are expected in development).

## Rollback Procedure (If Needed)

If migrations fail or cause issues:

### 1. Restore Database Backup

**PostgreSQL:**
```bash
psql -U username -d workstate < backup_YYYYMMDD_HHMMSS.sql
```

**SQLite:**
```bash
cp db.sqlite3.backup_YYYYMMDD_HHMMSS db.sqlite3
```

### 2. Roll Back to Specific Migration

If you need to undo specific migrations:

```bash
python manage.py migrate accounts 0001_initial
```

This rolls back to migration `0001_initial`, undoing any later migrations.

### 3. Show Migration

Review migration SQL before applying:

```bash
python manage.py sqlmigrate accounts 0001
```

## Production-Specific Steps

### 1. Use PostgreSQL

Switch from SQLite to PostgreSQL:

**Update .env:**
```env
DATABASE_URL=postgresql://username:password@localhost:5432/workstate
```

**Install psycopg2:**
```bash
pip install psycopg2-binary
```

**Run migrations:**
```bash
python manage.py migrate
```

### 2. Configure Production Email Backend

Update email settings for production:

**File:** `.env`
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@workstate.com
```

### 3. Configure Media Storage

For production, consider cloud storage (S3, etc.):

**Install boto3 (for AWS S3):**
```bash
pip install boto3 django-storages
```

**Update settings:**
```python
# settings.py
if not DEBUG:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
```

### 4. Set Up Web Server Media Serving

Configure nginx to serve media files:

**nginx.conf:**
```nginx
location /media/ {
    alias /path/to/workstate/media/;
}
```

## Troubleshooting

### Migration Fails with Error

**Issue:** Migration fails with database error

**Solution:**
1. Check database connection
2. Review migration file for issues
3. Try `python manage.py migrate --fake-initial` if models exist
4. Roll back and try again

### Email Verification Not Working

**Issue:** Verification emails not appearing in console

**Solution:**
1. Verify `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`
2. Check console/terminal output
3. Verify django-allauth is in `INSTALLED_APPS`
4. Check `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'`

### Media Uploads Fail

**Issue:** Avatar upload returns error

**Solution:**
1. Check media directory exists and has write permissions
2. Verify `MEDIA_ROOT` and `MEDIA_URL` in settings
3. Ensure media URL patterns are configured
4. Check file size limits (default 5MB)

### Timezone Not Activating

**Issue:** Dates showing in wrong timezone

**Solution:**
1. Verify `TimezoneMiddleware` is in `MIDDLEWARE`
2. Check `USE_TZ = True` in settings
3. Verify user preference timezone is set
4. Check template filters are using timezone-aware display

## Completion Checklist

Mark each item as complete:

- [ ] Database backup created (production)
- [ ] All migrations applied successfully
- [ ] No pending migrations remain
- [ ] Initial superuser created
- [ ] Superuser can log in to Django admin
- [ ] Email verification tested with console backend
- [ ] Test user registered and verified email
- [ ] Media directory exists with correct permissions
- [ ] Avatar upload tested and files saved correctly
- [ ] Timezone middleware configured in settings
- [ ] Timezone preference tested and working
- [ ] All tests pass
- [ ] No migration conflicts detected
- [ ] Static files collected (production)
- [ ] Security check reviewed
- [ ] Production database configured (if applicable)
- [ ] Production email backend configured (if applicable)
- [ ] Web server media serving configured (if applicable)

## Next Steps

After completing this checklist:

1. Review [Security Configuration Checklist](SECURITY_CHECKLIST.md)
2. Set up monitoring and logging
3. Configure backups
4. Test all user flows manually
5. Deploy to production environment

## Support

If you encounter issues:
- Review [Setup Guide](SETUP.md)
- Check [Admin Setup Guide](ADMIN_SETUP.md)
- Review Django documentation
- Check project issue tracker
