# Security Configuration Checklist

This checklist ensures that all security configurations for the Workstate authentication system are properly implemented and verified.

## Overview

This document verifies critical security settings including CSRF protection, password hashing, session security, file upload validation, and admin access controls.

## CSRF Protection

Cross-Site Request Forgery (CSRF) protection prevents unauthorized commands from being transmitted from a user that the web application trusts.

### 1. Verify CSRF Middleware Enabled

**File:** `workstate/settings.py`

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # Must be present
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

**Status:**
- [ ] `CsrfViewMiddleware` is present in `MIDDLEWARE`
- [ ] Middleware is positioned after `SessionMiddleware` and before views

### 2. Verify CSRF Tokens in Forms

All POST forms must include CSRF tokens.

**Check Template Forms:**

```bash
grep -r "{% csrf_token %}" templates/
```

**Expected:** All forms that use POST method include `{% csrf_token %}`

**Example:**
```django
<form method="post">
    {% csrf_token %}
    <!-- form fields -->
    <button type="submit">Submit</button>
</form>
```

**Status:**
- [ ] Registration form includes CSRF token
- [ ] Login form includes CSRF token
- [ ] Password reset forms include CSRF token
- [ ] Profile edit form includes CSRF token
- [ ] Preferences form includes CSRF token
- [ ] Admin action forms include CSRF token

### 3. Test CSRF Protection

**Manual Test:**

1. Open browser developer tools
2. Navigate to login page
3. Inspect form HTML
4. Locate hidden CSRF token input field
5. Verify token is present and non-empty

**Expected:**
```html
<input type="hidden" name="csrfmiddlewaretoken" value="...long-token...">
```

**Automated Test:**

```bash
python manage.py shell
```

```python
from django.test import Client

client = Client()
response = client.get('/accounts/login/')
print('csrfmiddlewaretoken' in response.content.decode())
# Should print: True
```

**Status:**
- [ ] CSRF tokens appear in all forms
- [ ] Form submission fails without valid CSRF token
- [ ] CSRF test passes

### 4. Production CSRF Settings

For production deployments:

**File:** `workstate/settings.py` or `.env`

```python
# Production only
if not DEBUG:
    CSRF_COOKIE_SECURE = True  # Only send cookie over HTTPS
    CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    CSRF_TRUSTED_ORIGINS = ['https://yourdomain.com']
```

**Status:**
- [ ] `CSRF_COOKIE_SECURE = True` in production
- [ ] `CSRF_COOKIE_HTTPONLY = True` configured
- [ ] `CSRF_TRUSTED_ORIGINS` set for production domain

## Password Hashing Verification

Django uses PBKDF2 algorithm with SHA256 hash for password hashing.

### 1. Verify Password Hashers Configuration

**File:** `workstate/settings.py`

```python
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',  # Default
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]
```

Django uses PBKDF2 by default if `PASSWORD_HASHERS` is not explicitly set.

**Status:**
- [ ] PBKDF2 is the first (default) password hasher
- [ ] No weak hashers (MD5, SHA1) are used as primary

### 2. Test Password Hashing

**Create Test User:**

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model

User = get_user_model()

# Create user with password
user = User.objects.create_user(
    email='hashtest@example.com',
    password='TestPassword123'
)

# Check hashed password
print(f"Hashed password: {user.password}")
```

**Expected Output:**
```
Hashed password: pbkdf2_sha256$260000$...long-hash...
```

The password should start with `pbkdf2_sha256$` indicating PBKDF2 with SHA256.

**Status:**
- [ ] Passwords are hashed using PBKDF2
- [ ] Hash includes salt (random component)
- [ ] Plain-text passwords are never stored

### 3. Verify Password Validation

**File:** `workstate/settings.py`

```python
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # Minimum 8 characters
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

**Status:**
- [ ] Minimum password length is 8 characters
- [ ] User attribute similarity check enabled
- [ ] Common password check enabled
- [ ] Numeric-only password check enabled

### 4. Test Password Validation

**Test Weak Passwords:**

```bash
python manage.py shell
```

```python
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# Test weak passwords
weak_passwords = ['12345678', 'password', 'abc']

for pwd in weak_passwords:
    try:
        validate_password(pwd)
        print(f"{pwd}: PASSED (should not happen!)")
    except ValidationError as e:
        print(f"{pwd}: REJECTED - {e}")
```

**Expected:** All weak passwords should be rejected.

**Status:**
- [ ] Short passwords (< 8 chars) are rejected
- [ ] Common passwords are rejected
- [ ] Numeric-only passwords are rejected

## Session Security Settings

Session security prevents session hijacking and unauthorized access.

### 1. Verify Session Configuration

**File:** `workstate/settings.py`

```python
# Session settings
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_NAME = 'sessionid'

# Production settings
if not DEBUG:
    SESSION_COOKIE_SECURE = True  # Only send over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
```

**Status:**
- [ ] `SESSION_COOKIE_AGE` is set (default: 2 weeks)
- [ ] Production: `SESSION_COOKIE_SECURE = True`
- [ ] Production: `SESSION_COOKIE_HTTPONLY = True`
- [ ] Production: `SESSION_COOKIE_SAMESITE = 'Lax'` or `'Strict'`

### 2. Test Session Timeout

**Manual Test:**

1. Log in to the application
2. Note the current time
3. Wait for session expiry (or set `SESSION_COOKIE_AGE` to 60 seconds for testing)
4. Try to access a protected page
5. Verify redirect to login page

**Status:**
- [ ] Sessions expire after configured time
- [ ] Expired sessions redirect to login

### 3. Test "Remember Me" Functionality

**Code Review:**

Check login view extends session for "Remember Me":

```python
# In login view
if form.cleaned_data.get('remember_me'):
    request.session.set_expiry(2592000)  # 30 days
else:
    request.session.set_expiry(1209600)  # 2 weeks
```

**Manual Test:**

1. Log in without "Remember Me"
2. Check session cookie expiry (should be 2 weeks)
3. Log out and log in with "Remember Me" checked
4. Check session cookie expiry (should be 30 days)

**Status:**
- [ ] "Remember Me" extends session to 30 days
- [ ] Default session is 2 weeks
- [ ] Session timeout logic works correctly

### 4. Account Lockout Protection

**Verify Lockout Logic:**

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from accounts.models import LoginAttempt

User = get_user_model()

# Get test user
user = User.objects.get(email='testuser@example.com')

# Check if account is locked
from accounts.views import is_account_locked

print(f"Is locked: {is_account_locked(user)}")

# Check failed attempts
attempts = LoginAttempt.objects.filter(
    user=user,
    is_successful=False
).count()
print(f"Failed attempts: {attempts}")
```

**Manual Test:**

1. Attempt to log in with wrong password 3 times
2. Verify account is locked
3. Check lockout message displays with unlock time
4. Wait 30 minutes (or modify timeout for testing)
5. Verify automatic unlock

**Status:**
- [ ] Account locks after 3 failed attempts
- [ ] Lockout message displays with unlock time
- [ ] Automatic unlock after 30 minutes
- [ ] Admin can manually unlock accounts

## File Upload Validation

Avatar uploads must be validated for type, size, and security.

### 1. Verify File Upload Settings

**File:** `accounts/forms.py` or `accounts/models.py`

```python
# Avatar field configuration
avatar = models.ImageField(
    upload_to='avatars/user_%d/',
    blank=True,
    null=True,
    validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif']),
        validate_file_size  # Max 5MB
    ]
)
```

**Status:**
- [ ] Only image files allowed (jpg, jpeg, png, gif)
- [ ] File size limit enforced (5MB maximum)
- [ ] Upload path is sanitized (no directory traversal)

### 2. Test File Type Validation

**Manual Test:**

1. Log in to application
2. Navigate to profile page
3. Try uploading a non-image file (e.g., .txt, .exe, .php)
4. Verify error message: "Invalid file type"

**Status:**
- [ ] Non-image files are rejected
- [ ] Error message displays for invalid types
- [ ] Only allowed extensions are accepted

### 3. Test File Size Validation

**Manual Test:**

1. Create a large image file (> 5MB)
2. Try uploading to profile
3. Verify error message: "File size exceeds 5MB"

**Status:**
- [ ] Large files (> 5MB) are rejected
- [ ] Error message displays for oversized files
- [ ] File size validation works correctly

### 4. Test Upload Path Security

**Verify Upload Paths:**

```bash
ls -la media/avatars/
```

**Expected:** Files should be organized by user ID and not contain any directory traversal characters.

**Example:**
```
media/avatars/user_1/avatar.jpg
media/avatars/user_2/profile.png
```

**Check for Security Issues:**

```bash
find media/ -name "*.php" -o -name "*.exe" -o -name "*.sh"
```

**Expected:** No executable files in media directory.

**Status:**
- [ ] Upload paths are sanitized
- [ ] No directory traversal possible
- [ ] No executable files in media directory
- [ ] Files organized by user ID

### 5. Verify Media URL Access

**Test Direct Access:**

1. Upload an avatar
2. Note the file URL (e.g., `/media/avatars/user_1/avatar.jpg`)
3. Try accessing the file directly in browser
4. Verify file is served (in development)

**Production Consideration:**

In production, configure web server to serve media files with appropriate security headers.

**Status:**
- [ ] Uploaded files are accessible to authenticated users
- [ ] Production web server configured for media serving
- [ ] Appropriate security headers set (X-Content-Type-Options, etc.)

## Admin Access Controls

Admin features must be restricted to authorized users only.

### 1. Verify Admin Permission Decorator

**File:** `accounts/decorators.py` or `accounts/views.py`

```python
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def admin_required(view_func):
    """
    Decorator that checks if user is staff (admin).
    """
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper
```

**Status:**
- [ ] `@admin_required` decorator exists
- [ ] Decorator checks `is_staff` flag
- [ ] Non-admin users get 403 Forbidden error

### 2. Test Admin Dashboard Access Control

**Manual Test:**

1. Log in as regular user (not admin)
2. Navigate to `/admin-dashboard/`
3. Verify 403 Forbidden error

**Expected:** Non-admin users cannot access admin dashboard.

**Test with Admin User:**

1. Log in as admin (is_staff=True)
2. Navigate to `/admin-dashboard/`
3. Verify dashboard loads successfully

**Status:**
- [ ] Regular users cannot access admin dashboard
- [ ] Admin users can access admin dashboard
- [ ] 403 error displays for unauthorized access

### 3. Test Admin Actions Access Control

**Manual Test Admin Actions:**

Test each admin action with non-admin user:

1. Try accessing `/admin-dashboard/users/1/unlock/` as regular user
2. Verify 403 Forbidden error
3. Repeat for other actions (reset-password, delete, toggle-admin)

**Status:**
- [ ] Unlock account action requires admin access
- [ ] Reset password action requires admin access
- [ ] Delete user action requires admin access
- [ ] Toggle admin action requires admin access
- [ ] All admin actions protected by `@admin_required`

### 4. Verify Django Admin Access

**Manual Test:**

1. Log out (or use incognito mode)
2. Navigate to `/admin/`
3. Verify redirect to login page

**Log in as Regular User:**

1. Log in with non-staff user
2. Try accessing `/admin/`
3. Verify "You do not have permission" message

**Log in as Admin:**

1. Log in with staff user (is_staff=True)
2. Access `/admin/`
3. Verify Django admin interface loads

**Status:**
- [ ] Unauthenticated users redirected to login
- [ ] Non-staff users cannot access Django admin
- [ ] Staff users can access Django admin
- [ ] Superusers have full admin access

### 5. Test Admin Privilege Escalation Prevention

**Verify Permission Checks:**

Check that regular users cannot grant themselves admin access:

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model

User = get_user_model()

# Create regular user
user = User.objects.create_user(
    email='regular@example.com',
    password='TestPassword123'
)

# Verify is_staff is False
print(f"Is staff: {user.is_staff}")  # Should be False

# Regular users should not be able to set is_staff via forms
# This should be protected in the form/view layer
```

**Status:**
- [ ] Regular users cannot grant themselves admin access
- [ ] Admin privilege changes only via authorized methods
- [ ] Profile/preferences forms do not expose `is_staff` field

## Additional Security Configurations

### 1. Security Headers

**File:** `workstate/settings.py`

```python
# Production security settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
```

**Status:**
- [ ] `SECURE_SSL_REDIRECT = True` in production
- [ ] `SECURE_BROWSER_XSS_FILTER = True`
- [ ] `SECURE_CONTENT_TYPE_NOSNIFF = True`
- [ ] HSTS headers configured
- [ ] `X_FRAME_OPTIONS = 'DENY'` or `'SAMEORIGIN'`

### 2. Secret Key Security

**Verify Secret Key:**

**File:** `.env` and `workstate/settings.py`

```python
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-in-production')
```

**Status:**
- [ ] Secret key loaded from environment variable
- [ ] Secret key not committed to version control
- [ ] Production secret key is strong and random (50+ characters)
- [ ] `.env` file is in `.gitignore`

### 3. Debug Mode

**Verify Debug Setting:**

```python
DEBUG = os.getenv('DEBUG', 'False') == 'True'
```

**Status:**
- [ ] `DEBUG = False` in production
- [ ] Debug mode controlled by environment variable
- [ ] Error pages do not expose sensitive information in production

### 4. Allowed Hosts

**File:** `workstate/settings.py`

```python
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
```

**Status:**
- [ ] `ALLOWED_HOSTS` is properly configured
- [ ] Production domain(s) listed
- [ ] `ALLOWED_HOSTS` not set to `['*']` in production

### 5. Database Connection Security

**Verify Database Configuration:**

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

**Status:**
- [ ] Database credentials loaded from environment
- [ ] Database credentials not in version control
- [ ] Database user has minimum required privileges
- [ ] Database connection uses SSL/TLS in production

## Security Testing

### 1. Run Django Security Check

```bash
python manage.py check --deploy
```

Review all warnings and errors. Address critical issues before deployment.

**Status:**
- [ ] Security check completed
- [ ] All critical issues resolved
- [ ] Warnings reviewed and addressed

### 2. Test for Common Vulnerabilities

**SQL Injection:**

All database queries use Django ORM, which prevents SQL injection by default.

**Status:**
- [ ] All queries use Django ORM
- [ ] No raw SQL queries without parameterization

**XSS (Cross-Site Scripting):**

Django templates auto-escape output by default.

**Status:**
- [ ] Template auto-escaping enabled (default)
- [ ] No use of `|safe` filter without sanitization

**CSRF:**

Verified above.

**Status:**
- [ ] CSRF protection enabled and tested

### 3. Password Reset Token Security

**Verify Token Generation:**

Django generates secure password reset tokens by default.

**Test Token Expiration:**

1. Request password reset
2. Wait for token expiration (default: 24 hours or check settings)
3. Try using expired token
4. Verify error message: "Token expired"

**Status:**
- [ ] Password reset tokens are cryptographically secure
- [ ] Tokens expire after configured time
- [ ] Expired tokens cannot be reused

## Completion Checklist

Mark each security area as verified:

### CSRF Protection
- [ ] CSRF middleware enabled
- [ ] All forms include CSRF tokens
- [ ] CSRF protection tested and working
- [ ] Production CSRF settings configured

### Password Hashing
- [ ] PBKDF2 hasher configured as default
- [ ] Password hashing tested and verified
- [ ] Password validation rules enforced
- [ ] Weak passwords rejected

### Session Security
- [ ] Session configuration reviewed
- [ ] Session timeout working
- [ ] "Remember Me" functionality tested
- [ ] Production session security settings configured
- [ ] Account lockout protection working

### File Upload Validation
- [ ] File type validation working
- [ ] File size limits enforced
- [ ] Upload path security verified
- [ ] No executable files in media directory

### Admin Access Controls
- [ ] Admin permission decorator implemented
- [ ] Admin dashboard access controlled
- [ ] Admin actions protected
- [ ] Django admin access restricted
- [ ] Privilege escalation prevented

### Additional Security
- [ ] Security headers configured for production
- [ ] Secret key secured and not in version control
- [ ] Debug mode disabled in production
- [ ] Allowed hosts configured
- [ ] Database credentials secured

### Security Testing
- [ ] Django security check passed
- [ ] Common vulnerabilities tested
- [ ] Password reset security verified

## Next Steps

After completing this security checklist:

1. Review all checkboxes and address any failures
2. Document any security exceptions or known issues
3. Set up security monitoring and logging
4. Schedule regular security audits
5. Keep Django and dependencies updated
6. Review and update security configurations quarterly

## Resources

- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)

## Support

For security concerns or questions:
- Review [Setup Guide](SETUP.md)
- Check Django security documentation
- Consult security best practices
- Report security issues responsibly
