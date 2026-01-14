# Admin User Setup Guide

This guide explains how to create and manage admin users in Workstate, including creating the first admin user, granting admin privileges to existing users, and accessing the admin dashboard.

## Overview

Workstate has two types of admin access:

1. **Django Admin**: Built-in Django administration interface for managing database models
2. **Admin Dashboard**: Custom user management interface for admin-specific operations

Admin users have `is_staff=True` flag set on their User account, which grants access to both interfaces.

## Creating the First Admin User

### Method 1: Using Django's createsuperuser Command (Recommended)

The easiest way to create the first admin user is using Django's management command:

```bash
python manage.py createsuperuser
```

**Interactive Prompts:**

1. **Email address**: Enter the admin user's email (used for login)
   ```
   Email address: admin@workstate.com
   ```

2. **Password**: Enter a secure password (minimum 8 characters)
   ```
   Password:
   Password (again):
   ```

**What Happens:**

The `createsuperuser` command automatically:
- Creates a User account with:
  - `email`: The email you provided
  - `is_staff=True`: Grants admin access
  - `is_superuser=True`: Grants all permissions
  - Password is hashed using PBKDF2
- Creates a UserProfile with default values:
  - `full_name`: Extracted from email or set to empty
  - `timezone`: UTC
  - Other fields blank
- Creates UserPreference with defaults:
  - `timezone`: UTC
  - `date_format`: MM/DD/YYYY
  - `time_format`: 12-hour
  - `week_start_day`: Sunday
- Creates a personal Workspace:
  - `name`: Random constellation name
  - `is_personal=True`
  - `owner`: The admin user

**Verification:**

You can verify the superuser was created successfully:

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

admin = User.objects.get(email='admin@workstate.com')
print(f"Is staff: {admin.is_staff}")  # Should be True
print(f"Is superuser: {admin.is_superuser}")  # Should be True
```

### Method 2: Using Django Shell

You can also create an admin user programmatically:

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model

User = get_user_model()

# Create superuser
admin = User.objects.create_superuser(
    email='admin@workstate.com',
    password='SecurePassword123'
)

print(f"Admin user created: {admin.email}")
print(f"Is staff: {admin.is_staff}")
print(f"Is superuser: {admin.is_superuser}")
```

**Note**: When using `create_superuser()`, the post-save signals should automatically create the associated UserProfile, UserPreference, and Workspace.

### Method 3: Promoting an Existing User to Admin (Django Admin)

If you already have a regular user account and want to make it an admin:

1. Log in to Django Admin at `/admin/` with an existing superuser account
2. Navigate to **Users** section
3. Click on the user you want to promote
4. Check the following boxes:
   - **Staff status**: Grants access to admin site
   - **Superuser status**: Grants all permissions (optional)
5. Click **Save**

## Granting Admin Privileges to Existing Users

### Method 1: Using the Admin Dashboard (Recommended)

The custom Admin Dashboard provides a user-friendly interface for managing admin privileges:

1. **Log in** as an admin user
2. Navigate to **Admin Dashboard** at `/admin-dashboard/`
3. Find the user in the user list (use search or filters)
4. Click **View Details** to open the user detail page
5. Click the **Grant Admin** button
6. Confirm the action
7. The user now has admin privileges

**What Happens:**
- Sets `is_staff=True` on the user's account
- User can now access both Django Admin and Admin Dashboard
- User appears in admin user lists
- Action is instantaneous (no email notification)

### Method 2: Using Django Admin

1. Log in to Django Admin at `/admin/`
2. Go to **Authentication and Authorization** > **Users**
3. Click on the user you want to grant admin access
4. Check the **Staff status** checkbox
5. (Optional) Check **Superuser status** for full permissions
6. Click **Save**

### Method 3: Using Django Shell

For programmatic access:

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model

User = get_user_model()

# Find the user
user = User.objects.get(email='user@example.com')

# Grant admin access
user.is_staff = True
user.save()

print(f"{user.email} is now an admin")
```

### Method 4: Using Management Command (Custom)

You can create a custom management command for granting admin access:

**File**: `accounts/management/commands/grant_admin.py`

```python
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Grant admin privileges to a user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email address')

    def handle(self, *args, **options):
        email = options['email']
        try:
            user = User.objects.get(email=email)
            user.is_staff = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully granted admin access to {email}')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} does not exist')
            )
```

**Usage:**
```bash
python manage.py grant_admin user@example.com
```

## Revoking Admin Privileges

### Using the Admin Dashboard

1. Log in as an admin user
2. Navigate to **Admin Dashboard**
3. Find the admin user in the list
4. Click **View Details**
5. Click the **Revoke Admin** button
6. Confirm the action

**What Happens:**
- Sets `is_staff=False` on the user's account
- User loses access to Django Admin and Admin Dashboard
- User retains their regular user account and data
- User can still log in and use the application as a regular user

### Using Django Admin

1. Log in to Django Admin
2. Go to **Users**
3. Click on the admin user
4. Uncheck the **Staff status** checkbox
5. Click **Save**

### Using Django Shell

```python
from django.contrib.auth import get_user_model

User = get_user_model()

user = User.objects.get(email='admin@example.com')
user.is_staff = False
user.save()

print(f"Admin access revoked for {user.email}")
```

## Admin Dashboard Access

### Accessing the Admin Dashboard

Once you have admin privileges, you can access the admin dashboard:

**URL**: `http://127.0.0.1:8000/admin-dashboard/`

**Login Required**: Must be logged in with an admin account

**Features Available:**
- View all registered users
- Search users by name or email
- Filter users by status (active, locked, unverified)
- View individual user details and preferences
- Unlock locked accounts
- Trigger password reset emails
- Delete user accounts
- Grant/revoke admin privileges
- View user login history

### Admin Dashboard Features

#### User List View

The main dashboard displays a table of all users with:
- Full name
- Email address
- Registration date
- Account status (active, locked, unverified)
- Quick action buttons

**Search**: Live search by name or email using HTMX

**Filters**:
- All users
- Active users only
- Locked accounts only
- Unverified accounts only

**Pagination**: 25 users per page

#### User Detail View

Click on any user to see detailed information:
- Full profile information
- User preferences (timezone, date/time formats)
- Workspace information
- Login history (last 10 attempts)
- Available actions

#### Admin Actions

**Unlock Account:**
- Manually unlock a locked user account
- Bypasses the 30-minute cooldown period
- Resets failed login attempt counter
- User can immediately log in

**Reset Password:**
- Trigger a password reset email for the user
- User receives standard password reset link
- No direct password change by admin (security)

**Delete User:**
- Permanently delete a user account
- Confirmation dialog warns of permanent action
- Cascade deletes:
  - UserProfile
  - UserPreference
  - Workspace(s)
  - LoginAttempts
- Cannot be undone

**Toggle Admin Privileges:**
- Grant or revoke admin access
- Button text changes based on current status
- Immediate effect (no confirmation)

### Accessing Django Admin

Django's built-in admin interface is also available:

**URL**: `http://127.0.0.1:8000/admin/`

**Features:**
- Full database model access
- Advanced filtering and searching
- Bulk actions
- Model inline editing
- Database-level operations

**When to Use:**
- Database maintenance
- Bulk operations
- Advanced queries
- Model debugging

**When to Use Admin Dashboard Instead:**
- User management tasks
- Account unlocking
- Password resets
- Granting admin access
- Better UX for common tasks

## Permission Checks and Security

### Access Control

Admin access is controlled through decorators and middleware:

**For Django Admin:**
- Requires `is_staff=True`
- Checked by Django's admin site

**For Admin Dashboard:**
- Requires `is_staff=True`
- Checked by `@admin_required` decorator
- Non-admin users get 403 Forbidden error

### Permission Levels

**Regular User (`is_staff=False`):**
- Can access their own profile and preferences
- Can manage their own workspaces
- Cannot access admin interfaces

**Staff User (`is_staff=True, is_superuser=False`):**
- Can access admin dashboard
- Can access Django admin
- Permissions limited to what's explicitly granted
- Cannot access all database models in Django admin

**Superuser (`is_staff=True, is_superuser=True`):**
- Full access to everything
- Can access all admin features
- Can manage other admins
- Can access all database models

### Security Best Practices

1. **Limit Superuser Accounts**: Only create superusers when absolutely necessary
2. **Use Staff Status**: For most admin users, `is_staff=True` without `is_superuser=True` is sufficient
3. **Regular Audits**: Periodically review who has admin access
4. **Strong Passwords**: Enforce strong passwords for admin accounts
5. **Two-Factor Authentication**: Consider adding 2FA for admin accounts (future enhancement)
6. **Audit Logging**: Track admin actions (future enhancement)

## Troubleshooting

### Cannot Access Admin Dashboard

**Issue**: Getting 403 Forbidden when accessing `/admin-dashboard/`

**Solution**:
1. Verify you're logged in
2. Check that your account has `is_staff=True`:
   ```python
   from django.contrib.auth import get_user_model
   User = get_user_model()
   user = User.objects.get(email='your-email@example.com')
   print(user.is_staff)  # Should be True
   ```
3. If False, grant admin privileges using one of the methods above

### Cannot Access Django Admin

**Issue**: Getting "You do not have permission to view this page"

**Solution**: Same as above - ensure `is_staff=True`

### Forgot Admin Password

**Issue**: Lost access to admin account

**Solution**:
1. Use another admin account to reset the password
2. Or use Django shell:
   ```python
   from django.contrib.auth import get_user_model
   User = get_user_model()
   admin = User.objects.get(email='admin@workstate.com')
   admin.set_password('NewPassword123')
   admin.save()
   ```

### No Admin Users Exist

**Issue**: Locked out of admin interfaces entirely

**Solution**: Create a new superuser using `python manage.py createsuperuser`

## Next Steps

After setting up admin users:

1. Review the [Security Configuration Checklist](SECURITY_CHECKLIST.md)
2. Set up user management workflows
3. Configure email notifications (production)
4. Review admin dashboard features
5. Train admin users on available actions

## Related Documentation

- [Development Setup Guide](SETUP.md)
- [Migration Checklist](MIGRATION_CHECKLIST.md)
- [Security Configuration](SECURITY_CHECKLIST.md)
