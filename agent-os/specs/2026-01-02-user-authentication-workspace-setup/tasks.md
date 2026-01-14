# Task Breakdown: User Authentication & Workspace Setup

## Overview
Total Task Groups: 6
Estimated Total Tasks: ~60-70 individual tasks

This feature establishes the foundational authentication system with email/password registration, login, profile management, and automatic personal workspace creation with timezone-aware preferences and comprehensive admin capabilities.

## Task List

### Database Layer

#### Task Group 1: User Models and Profile Extensions
**Dependencies:** None

- [x] 1.0 Complete user and profile database models
  - [x] 1.1 Write 2-8 focused tests for User and UserProfile models
    - Test user creation with required fields
    - Test email uniqueness constraint
    - Test password hashing on save
    - Test timezone default to UTC
    - Test profile relationship (one-to-one)
  - [x] 1.2 Extend Django User model or create UserProfile model
    - Fields: full_name, avatar (ImageField), job_title, company, phone_number
    - One-to-one relationship with Django User model
    - Timezone field with default UTC
    - created_at, updated_at timestamps
    - Follow Django model conventions
  - [x] 1.3 Create migration for user profile extension
    - Add indexes on user_id foreign key
    - Set NOT NULL constraints on required fields
    - Add cascade delete behavior
  - [x] 1.4 Ensure user model tests pass
    - Run ONLY the 2-8 tests written in 1.1
    - Verify migrations run successfully

**Acceptance Criteria:**
- Tests from 1.1 pass
- UserProfile model properly linked to User
- Migrations run without errors
- Password hashing works correctly

#### Task Group 2: Workspace Models
**Dependencies:** Task Group 1

- [ ] 2.0 Complete workspace database models
  - [ ] 2.1 Write 2-8 focused tests for Workspace model
    - Test workspace creation with user
    - Test workspace name uniqueness per user
    - Test automatic constellation name generation
    - Test workspace-user relationship
  - [ ] 2.2 Create Workspace model
    - Fields: name, owner (ForeignKey to User), is_personal (boolean)
    - Validations: name required, max length 100
    - created_at, updated_at timestamps
    - Unique constraint on (owner, name) combination
  - [ ] 2.3 Create ConstellationNameGenerator utility
    - Pre-defined list of constellation names (Orion, Andromeda, Cassiopeia, Lyra, Cygnus, Perseus, Draco, Ursa Major, Phoenix, Centaurus)
    - Random selection method
    - Handle duplicate names with numeric suffix if needed
    - Utility function: generate_constellation_name()
  - [ ] 2.4 Create migration for Workspace model
    - Add indexes on owner_id foreign key
    - Add unique constraint on (owner_id, name)
    - Set cascade delete on owner relationship
  - [ ] 2.5 Ensure workspace model tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify constellation name generator works
    - Verify migrations run successfully

**Acceptance Criteria:**
- Tests from 2.1 pass
- Workspace model properly linked to User
- Constellation name generator produces random names
- Migrations run without errors

#### Task Group 3: User Preferences and Security Models
**Dependencies:** Task Group 1

- [ ] 3.0 Complete user preferences and security tracking
  - [ ] 3.1 Write 2-8 focused tests for UserPreference and LoginAttempt models
    - Test preference creation with defaults
    - Test timezone, date format, time format options
    - Test failed login attempt tracking
    - Test account lockout after 3 attempts
    - Test auto-unlock after 30 minutes
  - [ ] 3.2 Create UserPreference model
    - Fields: user (OneToOne), timezone, date_format, time_format, week_start_day
    - Default values: timezone=UTC, date_format=MM/DD/YYYY, time_format=12-hour, week_start_day=Sunday
    - Choices for date_format, time_format, week_start_day
    - created_at, updated_at timestamps
  - [ ] 3.3 Create LoginAttempt model for account lockout tracking
    - Fields: user (ForeignKey), timestamp, is_successful (boolean), ip_address
    - Methods: is_account_locked(), get_lockout_end_time(), reset_failed_attempts()
    - Business logic: lock after 3 consecutive failures, unlock after 30 minutes
  - [ ] 3.4 Create migrations for UserPreference and LoginAttempt
    - Add indexes on user_id foreign keys
    - Add index on timestamp for LoginAttempt queries
    - Set cascade delete on user relationships
  - [ ] 3.5 Ensure preference and security model tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify lockout logic works correctly
    - Verify migrations run successfully

**Acceptance Criteria:**
- Tests from 3.1 pass
- UserPreference model has sensible defaults
- LoginAttempt tracking and lockout logic works
- Migrations run without errors

### Backend Authentication & Business Logic

#### Task Group 4: Registration and Email Verification
**Dependencies:** Task Groups 1, 2, 3

- [ ] 4.0 Complete user registration flow
  - [ ] 4.1 Write 2-8 focused tests for registration endpoints
    - Test successful registration with all fields
    - Test registration with minimal required fields
    - Test duplicate email detection and error
    - Test automatic workspace creation
    - Test email verification flow
  - [ ] 4.2 Install and configure django-allauth
    - Add to INSTALLED_APPS
    - Configure email verification settings
    - Set up email backend (console backend for development)
    - Configure account adapter for custom logic
  - [ ] 4.3 Create registration view and form
    - RegistrationForm with fields: email, password, password_confirmation, full_name, workspace_name (optional), job_title (optional), company (optional), phone_number (optional)
    - Password validation: minimum 8 characters
    - Email uniqueness validation
    - Handle duplicate email: redirect to login with email prepopulated and "Forgot password?" link
  - [ ] 4.4 Implement post-registration signal handler
    - Create UserProfile on user creation
    - Create UserPreference with auto-detected timezone defaults
    - Create personal Workspace with user-provided name or random constellation name
    - Mark workspace as is_personal=True
  - [ ] 4.5 Configure email verification templates
    - Email verification sent template
    - Email confirmation template
    - Account activation redirect to login
  - [ ] 4.6 Ensure registration tests pass
    - Run ONLY the 2-8 tests written in 4.1
    - Verify email verification emails sent
    - Verify workspace auto-creation works

**Acceptance Criteria:**
- Tests from 4.1 pass
- Users can register with email/password
- Email verification required before login
- Workspace automatically created on registration
- Duplicate emails handled gracefully

#### Task Group 5: Login and Account Lockout
**Dependencies:** Task Groups 1, 3

- [ ] 5.0 Complete login and account security
  - [ ] 5.1 Write 2-8 focused tests for login endpoints
    - Test successful login with correct credentials
    - Test failed login with incorrect password
    - Test account lockout after 3 failed attempts
    - Test lockout message display
    - Test auto-unlock after 30 minutes
    - Test "Remember Me" functionality
  - [ ] 5.2 Create custom login view with lockout checking
    - Check if account is locked before authentication
    - Display lockout message with unlock time if locked
    - Track failed login attempts in LoginAttempt model
    - Reset failed attempts counter on successful login
    - Implement "Remember Me" checkbox extending session
  - [ ] 5.3 Create LoginForm with email and password fields
    - Email field validation
    - Password field (not validated against complexity here, just checked)
    - "Remember Me" checkbox field
    - Custom clean method to check account lockout status
  - [ ] 5.4 Configure session settings for "Remember Me"
    - Default session expiry: 2 weeks
    - "Remember Me" session expiry: 30 days
    - Set SESSION_COOKIE_AGE based on checkbox
  - [ ] 5.5 Ensure login and lockout tests pass
    - Run ONLY the 2-8 tests written in 5.1
    - Verify lockout triggers after 3 failures
    - Verify auto-unlock after 30 minutes
    - Verify "Remember Me" extends session

**Acceptance Criteria:**
- Tests from 5.1 pass
- Login works with valid credentials
- Account locks after 3 failed attempts
- Lockout message shows unlock time
- Auto-unlock works after 30 minutes
- "Remember Me" extends session duration

#### Task Group 6: Password Reset Flow
**Dependencies:** Task Group 1

- [ ] 6.0 Complete password reset functionality
  - [ ] 6.1 Write 2-8 focused tests for password reset flow
    - Test password reset request with valid email
    - Test password reset email sent
    - Test password reset confirmation with valid token
    - Test password reset with invalid/expired token
    - Test new password validation (minimum 8 characters)
  - [ ] 6.2 Create password reset request view and form
    - Form with single email field
    - Send password reset email using Django's built-in PasswordResetView
    - Use Django's default token generation
    - Success message: "Password reset email sent"
  - [ ] 6.3 Create password reset confirmation view
    - Validate reset token
    - Form with new_password and new_password_confirmation fields
    - Apply password validation (minimum 8 characters)
    - Success: redirect to login with success message
    - Failure: display error and keep form
  - [ ] 6.4 Configure password reset email templates
    - Password reset email template with reset link
    - Password reset confirmation template
    - Success message template on login page
  - [ ] 6.5 Ensure password reset tests pass
    - Run ONLY the 2-8 tests written in 6.1
    - Verify reset emails sent
    - Verify tokens work correctly
    - Verify password validation applied

**Acceptance Criteria:**
- Tests from 6.1 pass
- Users can request password reset
- Reset emails sent with valid tokens
- Users can set new password
- Token expiration works correctly

#### Task Group 7: Profile Management
**Dependencies:** Task Groups 1, 3

- [ ] 7.0 Complete user profile management
  - [ ] 7.1 Write 2-8 focused tests for profile endpoints
    - Test profile view loads current user data
    - Test profile update with valid data
    - Test avatar upload and validation
    - Test email field is read-only
    - Test validation errors display inline
  - [ ] 7.2 Create profile view and template
    - Display current profile data
    - Form fields: full_name (editable), email (read-only), avatar (upload), timezone, job_title, company, phone_number
    - Avatar preview before and after upload
    - Single "Save Profile" button for all changes
  - [ ] 7.3 Create ProfileUpdateForm
    - All profile fields except email (read-only)
    - Avatar image validation: file type (jpg, png, gif), max size (5MB)
    - Timezone dropdown with all valid timezones
    - Field-specific validation with inline error display
  - [ ] 7.4 Implement profile update view logic
    - Load current user profile data
    - Handle form submission with validation
    - Save avatar file to media storage
    - Update UserProfile and User models
    - Display success message on save
  - [ ] 7.5 Ensure profile management tests pass
    - Run ONLY the 2-8 tests written in 7.1
    - Verify profile updates save correctly
    - Verify avatar uploads work
    - Verify email remains read-only

**Acceptance Criteria:**
- Tests from 7.1 pass
- Users can view their profile
- Users can update profile fields
- Avatar upload works with validation
- Email is read-only after verification
- Success/error messages display correctly

#### Task Group 8: User Preferences Management
**Dependencies:** Task Group 3

- [ ] 8.0 Complete user preferences functionality
  - [ ] 8.1 Write 2-8 focused tests for preferences endpoints
    - Test preferences view loads current settings
    - Test timezone auto-detection from browser
    - Test preferences update with valid choices
    - Test date/time format application across app
  - [ ] 8.2 Create preferences view and template
    - Form fields: timezone (auto-detected with manual override), date_format, time_format, week_start_day
    - Timezone auto-detection using Alpine.js (Intl.DateTimeFormat().resolvedOptions().timeZone)
    - Dropdown for date format: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD
    - Radio buttons for time format: 12-hour, 24-hour
    - Radio buttons for week start: Sunday, Monday, Saturday
    - Separate "Save Preferences" button
  - [ ] 8.3 Create PreferencesUpdateForm
    - Timezone field with dropdown of all valid timezones
    - Date format field with choices
    - Time format field with choices
    - Week start day field with choices
    - Validation for valid choices
  - [ ] 8.4 Implement preferences update view logic
    - Load current user preferences
    - Handle form submission
    - Update UserPreference model
    - Display success message
  - [ ] 8.5 Create template filters for date/time formatting
    - user_date filter: format dates according to user's date_format preference
    - user_time filter: format times according to user's time_format preference
    - user_datetime filter: combine date and time formatting
    - Apply user's timezone to all datetime displays
  - [ ] 8.6 Ensure preferences tests pass
    - Run ONLY the 2-8 tests written in 8.1
    - Verify preferences save correctly
    - Verify timezone auto-detection works
    - Verify date/time filters work

**Acceptance Criteria:**
- Tests from 8.1 pass
- Users can update preferences
- Timezone auto-detects from browser
- Date/time formats apply throughout app
- Success messages display correctly

### Admin Interface

#### Task Group 9: Admin User Management Dashboard
**Dependencies:** Task Groups 1, 3

- [ ] 9.0 Complete admin user management interface
  - [ ] 9.1 Write 2-8 focused tests for admin dashboard
    - Test admin access control (non-admins blocked)
    - Test user list display with pagination
    - Test search functionality
    - Test filter by status (active, locked, unverified)
    - Test view individual user details
  - [ ] 9.2 Create admin permission decorator
    - @admin_required decorator for admin-only views
    - Check user.is_staff or custom is_admin field
    - Redirect non-admins to 403 Forbidden page
  - [ ] 9.3 Create admin user list view
    - Display all users with: name, email, registration date, account status
    - Pagination (25 users per page)
    - Search by name or email
    - Filter dropdown: All, Active, Locked, Unverified
    - Link to individual user detail page
  - [ ] 9.4 Create admin user list template
    - Table layout with user data
    - HTMX-powered search (live search as user types)
    - Filter dropdown with HTMX partial reload
    - Pagination controls
    - Action buttons: View Details, Unlock, Reset Password, Delete
  - [ ] 9.5 Create admin user detail view
    - Display full user profile information
    - Display user preferences
    - Display workspace information
    - Display login history (last 10 attempts)
    - Action buttons: Unlock, Reset Password, Delete, Toggle Admin
  - [ ] 9.6 Ensure admin dashboard tests pass
    - Run ONLY the 2-8 tests written in 9.1
    - Verify permission checks work
    - Verify search and filters work
    - Verify pagination works

**Acceptance Criteria:**
- Tests from 9.1 pass
- Only admins can access dashboard
- User list displays correctly with pagination
- Search and filters work
- Individual user details accessible

#### Task Group 10: Admin Account Management Actions
**Dependencies:** Task Groups 1, 3, 5, 9

- [ ] 10.0 Complete admin account management capabilities
  - [ ] 10.1 Write 2-8 focused tests for admin actions
    - Test manual account unlock
    - Test trigger password reset email
    - Test delete user account with confirmation
    - Test assign admin privileges
    - Test revoke admin privileges
    - Test permission checks for all actions
  - [ ] 10.2 Create admin unlock account action
    - View to reset LoginAttempt failed attempts for user
    - HTMX endpoint returning success message
    - Update user detail page without full reload
    - Success message: "Account unlocked successfully"
  - [ ] 10.3 Create admin trigger password reset action
    - View to send password reset email to user
    - Use Django's send_password_reset_email function
    - HTMX endpoint returning confirmation
    - Success message: "Password reset email sent to [email]"
  - [ ] 10.4 Create admin delete user action
    - Confirmation dialog using Alpine.js
    - Warning: "This will permanently delete the user and all associated data"
    - HTMX DELETE request to delete endpoint
    - Cascade delete: UserProfile, UserPreference, Workspace, LoginAttempts
    - Redirect to user list with success message
  - [ ] 10.5 Create admin toggle admin privileges action
    - View to set/unset user.is_staff flag
    - HTMX endpoint returning updated status
    - Toggle button: "Grant Admin" / "Revoke Admin"
    - Update UI without full reload
    - Success message showing new status
  - [ ] 10.6 Ensure admin action tests pass
    - Run ONLY the 2-8 tests written in 10.1
    - Verify all actions work correctly
    - Verify permission checks prevent unauthorized access
    - Verify cascade deletes work

**Acceptance Criteria:**
- Tests from 10.1 pass
- Admins can unlock accounts
- Admins can trigger password resets
- Admins can delete users with confirmation
- Admins can grant/revoke admin privileges
- All actions have proper permission checks

### Frontend UI Components

#### Task Group 11: Registration and Login Pages
**Dependencies:** Task Groups 4, 5, 6

- [ ] 11.0 Complete registration and login UI
  - [ ] 11.1 Write 2-8 focused tests for registration/login UI
    - Test registration form renders all fields
    - Test login form renders with "Remember Me"
    - Test password visibility toggle
    - Test form validation error display
    - Test responsive layout on mobile
  - [ ] 11.2 Create registration page template
    - Form layout with Tailwind CSS styling
    - Fields: email, password, password confirmation, full name, workspace name (optional), job title (optional), company (optional), phone number (optional)
    - Password strength indicator using Alpine.js
    - Password visibility toggle (eye icon)
    - Submit button with loading state
    - Link to login page for existing users
    - Responsive design: mobile-first
  - [ ] 11.3 Create login page template
    - Form layout with Tailwind CSS styling
    - Fields: email, password
    - "Remember Me" checkbox
    - "Forgot Password?" link
    - Submit button with loading state
    - Link to registration page for new users
    - Account lockout message display area
    - Responsive design: mobile-first
  - [ ] 11.4 Create password reset request page
    - Form with email field
    - Submit button
    - Link back to login page
    - Success message display area
  - [ ] 11.5 Create password reset confirmation page
    - Form with new password and confirmation fields
    - Password visibility toggle
    - Password strength indicator
    - Submit button
    - Responsive design
  - [ ] 11.6 Add HTMX attributes for dynamic form submission
    - hx-post for form submissions
    - hx-target for error display areas
    - hx-swap for partial page updates
    - Loading indicators during submission
  - [ ] 11.7 Ensure UI component tests pass
    - Run ONLY the 2-8 tests written in 11.1
    - Verify responsive layouts work
    - Verify HTMX interactions work
    - Verify Alpine.js interactivity works

**Acceptance Criteria:**
- Tests from 11.1 pass
- Registration form fully functional
- Login form with "Remember Me" works
- Password reset flows work
- Forms are responsive and accessible
- HTMX provides smooth interactions

#### Task Group 12: Profile and Preferences Pages
**Dependencies:** Task Groups 7, 8

- [ ] 12.0 Complete profile and preferences UI
  - [ ] 12.1 Write 2-8 focused tests for profile/preferences UI
    - Test profile page renders user data
    - Test avatar upload preview
    - Test preferences page renders settings
    - Test timezone auto-detection
    - Test responsive layouts
  - [ ] 12.2 Create profile page template
    - Form layout with Tailwind CSS
    - Current avatar display with preview
    - Avatar upload with file input
    - File upload progress indicator (HTMX)
    - Fields: full_name, email (read-only with disabled styling), timezone, job_title, company, phone_number
    - "Save Profile" button
    - Inline validation error display
    - Success message display area
    - Responsive design
  - [ ] 12.3 Add avatar upload preview functionality
    - Alpine.js component for file preview
    - Display image preview before upload
    - Show file size and type
    - Validation feedback (file too large, wrong type)
  - [ ] 12.4 Create preferences page template
    - Form layout with Tailwind CSS
    - Timezone field with auto-detection indicator
    - Alpine.js script to detect browser timezone on page load
    - Date format dropdown with visual examples
    - Time format radio buttons with examples
    - Week start day radio buttons
    - "Save Preferences" button
    - Success message display area
    - Responsive design
  - [ ] 12.5 Implement timezone auto-detection
    - Alpine.js component using Intl.DateTimeFormat
    - Set hidden field value on page load
    - Display detected timezone to user
    - Allow manual override in dropdown
  - [ ] 12.6 Ensure profile/preferences UI tests pass
    - Run ONLY the 2-8 tests written in 12.1
    - Verify avatar preview works
    - Verify timezone auto-detection works
    - Verify responsive layouts work

**Acceptance Criteria:**
- Tests from 12.1 pass
- Profile page displays user data correctly
- Avatar upload with preview works
- Preferences page displays current settings
- Timezone auto-detection works
- Forms are responsive and accessible

#### Task Group 13: Admin Dashboard UI
**Dependencies:** Task Groups 9, 10

- [ ] 13.0 Complete admin dashboard UI
  - [ ] 13.1 Write 2-8 focused tests for admin UI
    - Test admin dashboard access control
    - Test user list table renders
    - Test search functionality UI
    - Test filter dropdown UI
    - Test action button functionality
  - [ ] 13.2 Create admin dashboard layout template
    - Navigation sidebar with admin sections
    - Main content area for user list
    - Header with page title and search bar
    - Responsive design with mobile menu
    - Tailwind CSS styling
  - [ ] 13.3 Create admin user list table component
    - Table with columns: Name, Email, Registration Date, Status, Actions
    - Status badges with color coding (green=active, red=locked, yellow=unverified)
    - Action buttons: View, Unlock, Reset Password, Delete
    - Pagination controls at bottom
    - HTMX for live search
    - Filter dropdown with HTMX partial reload
  - [ ] 13.4 Create admin user detail page template
    - User information card with profile data
    - Preferences display card
    - Workspace information card
    - Login history table (last 10 attempts)
    - Action buttons: Unlock Account, Reset Password, Delete User, Toggle Admin
    - Confirmation modals using Alpine.js
    - Responsive layout
  - [ ] 13.5 Add HTMX and Alpine.js interactivity
    - HTMX live search on user list
    - HTMX filter dropdown updates
    - Alpine.js confirmation dialogs for destructive actions
    - HTMX partial updates for action results
    - Loading states for all actions
  - [ ] 13.6 Ensure admin UI tests pass
    - Run ONLY the 2-8 tests written in 13.1
    - Verify permission checks work
    - Verify HTMX interactions work
    - Verify Alpine.js dialogs work

**Acceptance Criteria:**
- Tests from 13.1 pass
- Admin dashboard is accessible only to admins
- User list displays correctly
- Search and filters work smoothly
- Action buttons trigger correct functionality
- Confirmation dialogs prevent accidental deletions
- UI is responsive and accessible

### URL Routing and Configuration

#### Task Group 14: URL Configuration and Middleware
**Dependencies:** Task Groups 4, 5, 6, 7, 8, 9, 10

- [x] 14.0 Complete URL routing and Django configuration
  - [x] 14.1 Create URL patterns for authentication
    - /accounts/register/ - registration view
    - /accounts/login/ - login view
    - /accounts/logout/ - logout view
    - /accounts/password-reset/ - password reset request
    - /accounts/password-reset/confirm/<token>/ - password reset confirmation
    - /accounts/verify-email/<key>/ - email verification (django-allauth)
  - [x] 14.2 Create URL patterns for profile and preferences
    - /profile/ - user profile view
    - /profile/edit/ - profile edit form
    - /preferences/ - user preferences view
    - /preferences/edit/ - preferences edit form
  - [x] 14.3 Create URL patterns for admin
    - /admin-dashboard/ - admin user list
    - /admin-dashboard/users/<id>/ - admin user detail
    - /admin-dashboard/users/<id>/unlock/ - unlock account action
    - /admin-dashboard/users/<id>/reset-password/ - trigger password reset
    - /admin-dashboard/users/<id>/delete/ - delete user action
    - /admin-dashboard/users/<id>/toggle-admin/ - toggle admin privileges
  - [x] 14.4 Configure Django settings
    - Add django-allauth to INSTALLED_APPS
    - Configure AUTHENTICATION_BACKENDS
    - Set LOGIN_URL and LOGIN_REDIRECT_URL
    - Configure SESSION_COOKIE_AGE settings
    - Set up MEDIA_ROOT and MEDIA_URL for avatar uploads
    - Configure EMAIL_BACKEND (console for development)
  - [x] 14.5 Create custom middleware for timezone activation
    - Middleware to activate user's timezone for each request
    - Set timezone from UserPreference model
    - Apply to all authenticated requests
  - [x] 14.6 Test URL routing
    - Verify all URLs resolve correctly
    - Verify login_required decorators work
    - Verify admin_required decorators work
    - Verify middleware activates timezone

**Acceptance Criteria:**
- All URL patterns resolve correctly
- Authentication redirects work properly
- Login/admin decorators enforce access control
- Timezone middleware activates user timezone
- Django settings configured correctly

### Testing and Quality Assurance

#### Task Group 15: Integration Testing and Gap Analysis
**Dependencies:** Task Groups 1-14

- [ ] 15.0 Review existing tests and fill critical gaps only
  - [x] 15.1 Review tests from all previous task groups
    - Review database model tests (Groups 1, 2, 3: ~6-24 tests)
    - Review backend logic tests (Groups 4, 5, 6, 7, 8: ~10-40 tests)
    - Review admin functionality tests (Groups 9, 10: ~4-16 tests)
    - Review frontend UI tests (Groups 11, 12, 13: ~6-24 tests)
    - Total existing tests: approximately 26-104 tests
  - [ ] 15.2 Analyze test coverage gaps for this feature only
    - Identify critical end-to-end workflows lacking coverage
    - Focus on integration between layers (DB -> Backend -> Frontend)
    - Prioritize user registration to workspace creation flow
    - Prioritize login with lockout flow
    - Prioritize admin user management workflows
    - DO NOT assess entire application coverage
  - [ ] 15.3 Write up to 10 additional strategic integration tests
    - End-to-end registration: form submission -> email verification -> workspace creation -> login
    - End-to-end login lockout: 3 failed attempts -> lockout message -> 30min wait -> successful login
    - End-to-end password reset: request -> email -> token validation -> new password -> login
    - End-to-end profile update: edit profile -> avatar upload -> save -> verify display
    - End-to-end preferences: timezone auto-detect -> update preferences -> verify format application
    - End-to-end admin unlock: user locked -> admin unlocks -> user can login
    - End-to-end admin delete: admin deletes user -> cascade delete verified
    - Integration test: registration creates all related models (User, UserProfile, UserPreference, Workspace)
    - Integration test: timezone preference affects datetime display across app
    - Integration test: admin permission checks prevent non-admin access
  - [ ] 15.4 Run feature-specific test suite
    - Run ALL tests related to this authentication feature
    - Expected total: approximately 36-114 tests maximum
    - DO NOT run unrelated application tests
    - Verify all critical workflows pass
    - Fix any failing tests
  - [ ] 15.5 Manual testing checklist
    - Register new user with all fields
    - Register new user with minimal fields (verify constellation name)
    - Verify email and activate account
    - Login with correct credentials
    - Login with wrong password (verify lockout after 3 attempts)
    - Wait 30 minutes and verify auto-unlock
    - Request password reset and complete flow
    - Update profile with avatar upload
    - Update preferences and verify timezone/format changes
    - Test admin dashboard access (as admin and non-admin)
    - Test all admin actions (unlock, reset, delete, toggle admin)
    - Test responsive layouts on mobile, tablet, desktop
    - Test accessibility with keyboard navigation and screen reader

**Acceptance Criteria:**
- All feature-specific tests pass (36-114 tests total)
- Critical end-to-end workflows covered
- No more than 10 additional integration tests added
- Manual testing checklist completed
- All user flows work as expected

### Documentation and Deployment Preparation

#### Task Group 16: Documentation and Configuration
**Dependencies:** All previous task groups

- [ ] 16.0 Complete documentation and deployment preparation
  - [ ] 16.1 Create development setup documentation
    - Environment variables needed (.env.example)
    - Database migration commands
    - Initial superuser creation command
    - Media file storage configuration
    - Email backend configuration
  - [ ] 16.2 Document constellation name generator
    - List of constellation names used
    - How to add/modify constellation names
    - Duplicate handling strategy
  - [ ] 16.3 Create admin user setup guide
    - How to create first admin user
    - How to grant admin privileges to existing users
    - Admin dashboard access instructions
  - [ ] 16.4 Update project README
    - Add authentication feature description
    - Add workspace auto-creation explanation
    - Add user preferences documentation
    - Add admin capabilities overview
  - [ ] 16.5 Create migration checklist
    - Run migrations in correct order
    - Create initial superuser
    - Test email verification (console backend)
    - Verify media upload directory created
    - Test timezone middleware
  - [ ] 16.6 Security configuration checklist
    - CSRF protection enabled
    - PBKDF2 password hashing verified
    - Session security settings reviewed
    - File upload validation confirmed
    - Admin access controls verified

**Acceptance Criteria:**
- Documentation complete and accurate
- Setup instructions tested
- Security configurations verified
- Migration checklist completed
- Feature ready for deployment

## Execution Order

Recommended implementation sequence:

1. **Database Layer** (Task Groups 1-3): Establish data models for users, profiles, workspaces, preferences, and security tracking
2. **Backend Authentication** (Task Groups 4-6): Implement registration, login, and password reset flows
3. **Backend Profile & Preferences** (Task Groups 7-8): Build profile management and user preferences functionality
4. **Admin Interface Backend** (Task Groups 9-10): Create admin dashboard and account management capabilities
5. **Frontend UI** (Task Groups 11-13): Build all user-facing pages and admin dashboard UI
6. **Configuration** (Task Group 14): Set up URL routing, middleware, and Django settings
7. **Testing & Documentation** (Task Groups 15-16): Fill test gaps, verify integration, and complete documentation

## Key Technical Decisions

### Tech Stack Alignment
- **Backend**: Django with django-allauth for email verification
- **Frontend**: HTMX for dynamic interactions, Alpine.js for client-side interactivity, Tailwind CSS for styling
- **Database**: PostgreSQL with Django ORM
- **Authentication**: Django's built-in auth system with PBKDF2 password hashing
- **Testing**: pytest for all test cases

### Design Patterns
- **Model Layer**: Django models with proper relationships, validations, and timestamps
- **View Layer**: Django function-based or class-based views with decorators for access control
- **Template Layer**: Django templates with HTMX attributes and Alpine.js components
- **Forms**: Django forms with custom validation
- **Signals**: Post-save signals for automatic workspace creation

### Security Measures
- Email verification required before account activation
- Password hashing with PBKDF2 and automatic salting
- Account lockout after 3 failed login attempts
- 30-minute auto-unlock cooldown
- CSRF protection on all forms
- Admin-only access controls for sensitive operations
- File upload validation for avatars

### Performance Considerations
- Database indexes on foreign keys and frequently queried fields
- Efficient queries using Django ORM select_related and prefetch_related
- Pagination on admin user list (25 per page)
- HTMX for partial page updates reducing server load
- Timezone middleware for proper datetime handling

## Notes

- This is the foundational authentication feature for Workstate
- All future features will build upon these authentication patterns
- Constellation name generator adds a unique, delightful touch to workspace creation
- Admin capabilities provide essential platform management tools
- Timezone-aware datetime display ensures accurate time tracking globally
- HTMX and Alpine.js provide smooth, modern UX without heavy JavaScript frameworks
- Testing strategy focuses on critical workflows with minimal test count during development
