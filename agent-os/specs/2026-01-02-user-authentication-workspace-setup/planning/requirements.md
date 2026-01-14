# Spec Requirements: User Authentication & Workspace Setup

## Initial Description
Complete user registration, login, profile management, and personal workspace creation with timezone and preference settings.

This is the first feature from the roadmap covering the foundational authentication and workspace setup functionality for Workstate.

## Requirements Discussion

### First Round Questions

**Q1:** I'm assuming user registration will include email/password as the primary method with email verification required before access. Should we also include OAuth providers (Google, GitHub) in this initial implementation, or focus solely on email/password authentication first?

**Answer:** Focus solely on email/password authentication first (OAuth later)

**Q2:** For password requirements, I'm thinking we should enforce minimum 8 characters with at least one uppercase, one lowercase, one number, and one special character. Should we use these standard requirements, or do you have different password complexity rules in mind?

**Answer:** Enforce minimum 8 characters with complicated password generation logic using SALT methods

**Q3:** I assume each user will automatically get a personal workspace created upon successful registration with a default name like "My Workspace" or their username. Should users be able to customize the workspace name during signup, or should this be editable only after account creation?

**Answer:** Can specify during signup (optional), editable after account creation. If empty, create one with a name using constellation names

**Q4:** For user profile management, I'm planning to include: full name, email (read-only after verification), timezone selection, and avatar upload. Are there any other profile fields you want included in this initial implementation (e.g., job title, company, phone number)?

**Answer:** Include full name, email (read-only after verification), timezone selection, avatar upload, job title, company, and phone number

**Q5:** Regarding timezone settings, I assume we'll use this to display all dates and times in the user's local timezone throughout the application. Should the timezone default to auto-detection based on browser settings with the option to override, or require manual selection during registration?

**Answer:** Auto-detection based on browser settings with option to override

**Q6:** For the login flow, I'm thinking we should include "Remember Me" functionality (extends session duration) and "Forgot Password" with email-based password reset. Should we also include account lockout after X failed login attempts for security, or keep it simple for now?

**Answer:** Yes, auto lockout after 3 failed attempts, can be re-enabled after 30 minutes

**Q7:** I assume profile changes (name, timezone, avatar) should be saved individually with immediate feedback, rather than requiring a "Save Profile" button for all changes at once. Is that the preferred UX pattern?

**Answer:** Save all changes together with a "Save Profile" button

**Q8:** What should happen if a user tries to register with an email that's already in use - show a generic "email already exists" error, or provide a "login instead" link to avoid account enumeration concerns?

**Answer:** Display generic error message and redirect to login page

**Q9:** For this initial implementation, are we including any administrative capabilities (like viewing all users, disabling accounts), or is this purely focused on the end-user authentication and profile experience?

**Answer:** Yes, need admin capabilities (viewing all users, disabling accounts)

**Q10:** Should we include any user preference settings beyond timezone in this initial scope (e.g., date format, time format, week start day), or save those for a future preferences/settings feature?

**Answer:** Yes, include date format, time format, week start day in this initial scope

### Existing Code to Reference

No similar existing features identified for reference.

### Follow-up Questions

**Follow-up 1:** For the password SALT generation, I assume we'll use Django's built-in PBKDF2 password hashing (which includes salting automatically). This is the Django default and is secure. Should we stick with this standard Django approach, or do you have specific salting/hashing requirements beyond the framework's defaults?

**Answer:** Use Django's built-in PBKDF2 password hashing (Django standard)

**Follow-up 2:** You mentioned using "constellation names" for default workspace names when users don't provide one. Should we use a randomized constellation name (e.g., "Orion", "Andromeda", "Cassiopeia") for each new user, or follow a different pattern like "User's Workspace" or their email prefix?

**Answer:** Use randomized constellation names if not explicitly provided by the user

**Follow-up 3:** For the account lockout after 3 failed attempts with 30-minute auto-unlock - should we send an email notification to the user when their account gets locked, or just display a message on the login screen? Also, should there be a "Contact Support" or manual unlock option, or rely solely on the 30-minute timer?

**Answer:** Display a message to the user that account is locked and can retry after 30 minutes (no email notification since email support not enabled yet)

**Follow-up 4:** For admin capabilities, should admins be able to: View all user profiles and their details? Manually unlock locked accounts? Reset user passwords (send password reset emails)? Delete user accounts? Assign/revoke admin privileges to other users?

**Answer:** Include ALL admin features in initial scope:
- View all user profiles and their details: YES
- Manually unlock locked accounts: YES
- Reset user passwords (send password reset emails): YES
- Delete user accounts: YES
- Assign/revoke admin privileges to other users: YES

**Follow-up 5:** For job title, company, and phone number fields - should these be optional or required during registration? I'm assuming they're optional and can be filled in later via profile management. Is that correct?

**Answer:** Job title, company, and phone number are optional at registration time (can be filled in later)

**Follow-up 6:** When you say "redirect to login page" for duplicate email registration, should we also display a "Forgot password?" link on that login page in case they actually forgot they had an account, or just a standard login form?

**Answer:** Display login form with email prepopulated, allow user to enter password, and include "Forgot password?" link

## Visual Assets

### Files Provided:
No visual assets provided.

### Visual Insights:
No visual assets provided.

## Requirements Summary

### Functional Requirements

#### User Registration
- Email/password authentication only (OAuth deferred to future implementation)
- Email verification required before account access
- Password requirements: minimum 8 characters enforced
- Password hashing: Django's built-in PBKDF2 with automatic salting
- Registration form fields:
  - Email (required)
  - Password (required, with confirmation field)
  - Full name (required)
  - Workspace name (optional - uses random constellation name if not provided)
  - Job title (optional)
  - Company (optional)
  - Phone number (optional)
- Duplicate email handling: Display error message and redirect to login page with email prepopulated
- Automatic personal workspace creation upon successful registration
- Workspace naming logic: User-provided name OR random constellation name (e.g., "Orion", "Andromeda", "Cassiopeia")

#### User Login
- Email/password authentication
- "Remember Me" checkbox to extend session duration
- Account lockout after 3 failed login attempts
- Locked account auto-unlock after 30 minutes
- Lockout message displayed on login screen (no email notification)
- "Forgot Password" link available on login page

#### Password Reset
- "Forgot Password" flow with email-based password reset
- Password reset link sent to registered email address
- Reset link expiration (standard Django token expiration)

#### User Profile Management
- Profile fields:
  - Full name (editable)
  - Email (read-only after verification)
  - Avatar upload (image file)
  - Timezone selection (auto-detected with manual override option)
  - Job title (optional, editable)
  - Company (optional, editable)
  - Phone number (optional, editable)
- Profile changes saved together via "Save Profile" button (not individually)
- Validation and error feedback on profile update

#### Workspace Management
- Personal workspace created automatically on registration
- Workspace name editable after account creation
- Workspace serves as container for user's tasks, projects, and time entries

#### User Preferences
- Timezone setting (auto-detected from browser, manually overridable)
- Date format selection (e.g., MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD)
- Time format selection (12-hour vs 24-hour)
- Week start day (Sunday, Monday, Saturday)
- Preferences saved together via "Save Preferences" button

#### Admin Capabilities
- Admin user role with elevated privileges
- Admin dashboard/interface to manage users
- Admin features:
  - View all user profiles and their details
  - Manually unlock locked user accounts
  - Reset user passwords (trigger password reset email)
  - Delete user accounts (with confirmation)
  - Assign admin privileges to users
  - Revoke admin privileges from users
- Admin access control and permission checks

### Reusability Opportunities

No existing components or patterns identified since this is the first feature implementation.

Future features should reference:
- Authentication patterns established here
- Form validation and error handling approaches
- Profile management UI patterns
- Admin interface patterns
- User model and database schema

### Scope Boundaries

**In Scope:**
- Email/password authentication system
- User registration with email verification
- User login with account lockout security
- Password reset functionality
- User profile management (full name, email, avatar, timezone, job title, company, phone)
- Personal workspace automatic creation
- Workspace naming (user-provided or random constellation names)
- User preference settings (timezone, date format, time format, week start day)
- Admin capabilities (view users, unlock accounts, reset passwords, delete users, manage admin roles)
- Form validation and error handling
- Session management with "Remember Me" functionality

**Out of Scope:**
- OAuth provider authentication (Google, GitHub) - future feature
- Email notifications for account lockout - deferred until email system configured
- Two-factor authentication (2FA) - future security enhancement
- Team/shared workspace creation - covered in future roadmap item #22
- User invitations and team collaboration - covered in future roadmap items
- Advanced admin analytics or user activity tracking
- LDAP/SSO enterprise authentication - future feature
- Account deletion by users themselves (only admin can delete)
- Profile picture editing/cropping tools (upload only)
- Custom constellation name lists or branding

### Technical Considerations

#### Backend (Django/Python)
- Django's built-in authentication system as foundation
- Django User model extension for additional profile fields (or separate UserProfile model)
- django-allauth for email verification workflows
- PBKDF2 password hashing (Django default)
- Account lockout tracking (failed login attempts, lockout timestamp)
- Workspace model with one-to-one relationship to User
- Timezone handling using pytz library
- Constellation name generator/randomizer utility
- Admin permissions using Django's built-in permission system

#### Frontend (HTMX + Alpine.js + Tailwind CSS)
- Registration form with client-side and server-side validation
- Login form with "Remember Me" checkbox
- Password reset request and confirmation flows
- Profile edit form with avatar upload preview
- Preferences form with timezone auto-detection
- Admin user management interface
- Form error display and success messaging
- Responsive design (mobile-first)
- Accessibility compliance (semantic HTML, ARIA labels, keyboard navigation)

#### Database (PostgreSQL)
- User table with extended fields (or separate UserProfile table)
- Workspace table with foreign key to User
- UserPreference table for settings (or JSONB field on User/UserProfile)
- Failed login attempt tracking (timestamp, count)
- Account lockout status fields
- Indexes on email (unique), user_id foreign keys
- Timestamps (created_at, updated_at) on all tables

#### Security
- Email verification before account activation
- Password complexity validation (minimum 8 characters)
- PBKDF2 password hashing with salt
- Account lockout after 3 failed attempts (30-minute cooldown)
- CSRF protection on all forms
- SQL injection prevention via ORM
- XSS prevention via template auto-escaping
- Secure session handling
- Admin-only access control for admin endpoints

#### File Storage
- Avatar image uploads stored in media folder
- Image validation (file type, size limits)
- Secure file serving (no direct path exposure)
- Optional cloud storage integration (S3-compatible) in future

#### Email Integration
- Email verification emails (account activation)
- Password reset emails
- Admin-triggered password reset emails
- Note: Account lockout notifications deferred until email system fully configured

#### Constellation Name Generation
- Pre-defined list of constellation names
- Random selection algorithm to avoid duplicates (or accept collisions with numeric suffix)
- Examples: "Orion", "Andromeda", "Cassiopeia", "Lyra", "Cygnus", "Perseus", "Draco", "Ursa Major", etc.

#### Standards Compliance
- RESTful API patterns (if API endpoints created)
- Mobile-first responsive design
- WCAG accessibility standards
- Django coding conventions
- Tailwind CSS utility-first approach
- HTMX for dynamic interactions without full page reloads
- Minimal tests for core user flows (registration, login, profile update, admin actions)
