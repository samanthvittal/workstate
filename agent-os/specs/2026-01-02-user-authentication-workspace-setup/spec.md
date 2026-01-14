# Specification: User Authentication & Workspace Setup

## Goal
Establish foundational authentication system with email/password registration, login, profile management, and automatic personal workspace creation with timezone-aware preferences and admin capabilities for user management.

## User Stories
- As a new user, I want to register with my email and password, verify my email, and have a personal workspace automatically created so that I can start tracking my time immediately
- As a registered user, I want to log in securely with account lockout protection and manage my profile settings including timezone and preferences so that I can customize my experience
- As an admin, I want to view and manage all users, unlock accounts, reset passwords, and assign admin privileges so that I can maintain platform security and assist users

## Specific Requirements

**User Registration with Email Verification**
- Registration form with required fields: email, password, password confirmation, full name
- Optional fields during registration: workspace name, job title, company, phone number
- Password validation enforcing minimum 8 characters
- Django's built-in PBKDF2 password hashing with automatic salting
- Email verification required before account activation
- Duplicate email detection displaying error and redirecting to login with email prepopulated
- "Forgot password?" link displayed on login redirect for duplicate emails
- Automatic personal workspace creation upon successful email verification

**Workspace Automatic Creation and Naming**
- Single personal workspace created automatically during registration
- User-provided workspace name used if specified during signup
- Random constellation name assigned if no workspace name provided (e.g., "Orion", "Andromeda", "Cassiopeia", "Lyra", "Cygnus")
- Constellation name randomizer utility selecting from pre-defined list
- Workspace name editable after account creation
- Workspace serves as container for user's tasks, projects, and time entries

**Secure Login with Account Lockout**
- Email/password authentication form
- "Remember Me" checkbox extending session duration beyond default
- Failed login attempt tracking per user account
- Account lockout after 3 consecutive failed login attempts
- Automatic account unlock after 30-minute cooldown period
- Lockout message displayed on login screen informing user of 30-minute wait
- No email notification for lockout (email system not yet configured)
- "Forgot Password" link available on login page

**Password Reset Flow**
- "Forgot Password" link triggering email-based password reset
- Password reset email sent to registered email address
- Reset link with Django token expiration (standard Django timing)
- Password reset confirmation page with new password entry
- Password validation applied to new password (minimum 8 characters)
- Successful reset redirects to login page with success message

**User Profile Management**
- Profile edit form with fields: full name (editable), email (read-only after verification), avatar upload, timezone, job title, company, phone number
- Avatar image upload with file type and size validation
- All profile changes saved together via single "Save Profile" button
- Field-specific validation errors displayed inline
- Success message displayed after successful profile update
- Avatar preview before and after upload

**Timezone and User Preferences**
- Timezone auto-detection from browser settings on registration
- Timezone selection dropdown with manual override option
- Date format preference selection (MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD)
- Time format preference selection (12-hour, 24-hour)
- Week start day preference selection (Sunday, Monday, Saturday)
- Separate "Save Preferences" button for preference changes
- All dates and times throughout application displayed in user's selected timezone and format

**Admin User Management Dashboard**
- Admin-only interface accessible to users with admin role
- User list view displaying all registered users with key details (name, email, registration date, account status)
- Pagination and search functionality for user list
- Filter users by status (active, locked, unverified)
- View individual user profile details from admin dashboard

**Admin Account Management Capabilities**
- Manually unlock locked user accounts bypassing 30-minute cooldown
- Trigger password reset email for any user account
- Delete user accounts with confirmation dialog warning of permanent action
- Assign admin privileges to regular users
- Revoke admin privileges from existing admins
- Permission checks preventing non-admin users from accessing admin features

## Visual Design
No visual assets provided.

## Existing Code to Leverage

**Django Built-in Authentication System**
- Django's User model as foundation for user accounts
- Django's authentication backends for login/logout functionality
- Django's built-in PBKDF2 password hashing
- Django's password validation framework for enforcing password rules
- Django's permission system for admin role management

**Django Allauth for Email Verification**
- django-allauth library for email verification workflows
- Email confirmation token generation and validation
- Account activation after email verification
- Integration with Django's authentication system

**Tailwind CSS Utility Classes**
- Form styling with Tailwind utility classes
- Responsive design utilities for mobile-first approach
- Component styling without custom CSS

**HTMX for Dynamic Interactions**
- Form submission without full page reload
- Inline validation error display
- Avatar upload preview without JavaScript
- Admin actions (unlock, delete) with HTMX requests

**Alpine.js for Client-side Interactivity**
- Timezone auto-detection from browser
- Password visibility toggle
- Form field show/hide logic
- Confirmation dialogs for destructive actions

## Out of Scope
- OAuth provider authentication (Google, GitHub, Microsoft) - deferred to future implementation
- Email notifications for account lockout events - requires email system configuration
- Two-factor authentication (2FA) or multi-factor authentication - future security enhancement
- Team workspace creation or shared workspaces - covered in roadmap item #22
- User invitation system for team collaboration - future collaboration feature
- Advanced admin analytics dashboard or user activity tracking
- LDAP or SSO integration for enterprise authentication
- Account self-deletion by users (only admin can delete accounts)
- Advanced avatar editing tools (cropping, filters, rotation) - upload only in initial scope
- Custom constellation name lists or branded workspace naming schemes
- User impersonation feature for admin debugging
- Audit log of admin actions on user accounts - future compliance feature
