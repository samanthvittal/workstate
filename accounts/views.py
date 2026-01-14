"""
Views for user authentication and password reset.
"""
from django.contrib.auth import views as auth_views, login as auth_login, logout as auth_logout
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q

from .forms import (
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    ProfileUpdateForm,
    PreferencesUpdateForm,
    LoginForm
)
from .models import UserProfile, UserPreference, LoginAttempt, Workspace
from .decorators import admin_required


# Authentication Views

@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Custom login view with account lockout checking and "Remember Me" functionality.
    Records failed login attempts and enforces account lockout after 3 failures.
    """
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')

    # Get email from query parameter (for duplicate registration redirects)
    prepopulated_email = request.GET.get('email', '')

    if request.method == 'POST':
        form = LoginForm(request.POST, request=request)

        if form.is_valid():
            user = form.get_user()

            # Record successful login attempt
            ip_address = form.get_client_ip()
            LoginAttempt.objects.create(
                user=user,
                is_successful=True,
                ip_address=ip_address
            )

            # Log the user in
            auth_login(request, user)

            # Handle "Remember Me" checkbox
            remember_me = form.cleaned_data.get('remember_me', False)
            if remember_me:
                # Set session to expire in 30 days (2592000 seconds)
                request.session.set_expiry(2592000)
            else:
                # Use default session expiry (30 minutes = 1800 seconds)
                request.session.set_expiry(1800)

            # Redirect to next page or dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)

    else:
        # Prepopulate email if provided in query parameter
        initial_data = {'email': prepopulated_email} if prepopulated_email else {}
        form = LoginForm(request=request, initial=initial_data)

    context = {
        'form': form,
        'prepopulated_email': prepopulated_email,
    }

    return render(request, 'accounts/login.html', context)


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """
    Custom logout view that accepts both GET and POST requests.
    Logs out the user and redirects to login page.
    """
    auth_logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('accounts:login')


class PasswordResetView(auth_views.PasswordResetView):
    """
    View for requesting password reset.
    Sends password reset email using Django's built-in functionality.
    """
    form_class = CustomPasswordResetForm
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')

    def form_valid(self, form):
        """Add success message when form is valid."""
        messages.success(self.request, 'Password reset email sent')
        return super().form_valid(form)


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    """
    View displayed after password reset email has been sent.
    """
    template_name = 'accounts/password_reset_done.html'


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """
    View for confirming password reset with token.
    Validates reset token and allows user to set new password.
    """
    form_class = CustomSetPasswordForm
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')

    def form_valid(self, form):
        """Add success message when password is reset successfully."""
        messages.success(self.request, 'Your password has been reset successfully. You can now log in with your new password.')
        return super().form_valid(form)

    def form_invalid(self, form):
        """Add error message when form validation fails."""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    """
    View displayed after password has been reset successfully.
    """
    template_name = 'accounts/password_reset_complete.html'


# Profile and Preferences Views

@login_required
@require_http_methods(["GET"])
def profile_view(request):
    """
    Display user profile information.
    Shows current profile data with links to edit.
    """
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    context = {
        'profile': profile,
        'user': request.user,
    }

    return render(request, 'accounts/profile.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def profile_update_view(request):
    """
    Handle profile update form submission.
    Displays form and processes updates to user profile.
    """
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=profile,
            user=request.user
        )

        if form.is_valid():
            # Save profile updates
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()

            # Add success message
            messages.success(request, 'Your profile has been updated successfully.')

            # Redirect to profile view
            return redirect('accounts:profile')
    else:
        # Display form with current data
        form = ProfileUpdateForm(instance=profile, user=request.user)

    context = {
        'form': form,
        'profile': profile,
        'user': request.user,
    }

    return render(request, 'accounts/profile_update.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def preferences_view(request):
    """
    Display and update user preferences.
    Handles timezone, date format, time format, and week start day preferences.
    """
    # Get or create user preferences
    preference, created = UserPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = PreferencesUpdateForm(request.POST, instance=preference)

        if form.is_valid():
            # Save preference updates
            preference = form.save(commit=False)
            preference.user = request.user
            preference.save()

            # Add success message
            messages.success(request, 'Your preferences have been updated successfully.')

            # Redirect to preferences view to show updated settings
            return redirect('accounts:preferences')
    else:
        # Display form with current preferences
        form = PreferencesUpdateForm(instance=preference)

    context = {
        'form': form,
        'preference': preference,
        'user': request.user,
    }

    return render(request, 'accounts/preferences.html', context)


# Admin Dashboard Views

@admin_required
@require_http_methods(["GET"])
def admin_user_list(request):
    """
    Admin dashboard showing all users with search, filter, and pagination.
    Supports live search via HTMX and status filtering.
    """
    # Get all users with profiles
    users = User.objects.select_related('profile').all()

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(profile__full_name__icontains=search_query)
        )

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'locked':
        # Filter locked users
        locked_user_ids = []
        for user in users:
            if LoginAttempt.is_account_locked(user):
                locked_user_ids.append(user.id)
        users = users.filter(id__in=locked_user_ids)
    elif status_filter == 'unverified':
        users = users.filter(is_active=False)

    # Pagination (25 users per page)
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Add status information to each user
    for user in page_obj:
        user.is_locked = LoginAttempt.is_account_locked(user)
        if user.is_locked:
            user.status = 'locked'
        elif user.is_active:
            user.status = 'active'
        else:
            user.status = 'unverified'

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }

    # Return partial template for HTMX requests
    if request.headers.get('HX-Request'):
        return render(request, 'accounts/admin_user_list_partial.html', context)

    return render(request, 'accounts/admin_user_list.html', context)


@admin_required
@require_http_methods(["GET"])
def admin_user_detail(request, pk):
    """
    Admin view showing detailed information about a specific user.
    Displays profile, preferences, workspaces, and login history.
    """
    user = get_object_or_404(User, pk=pk)

    # Get or create related objects
    profile, _ = UserProfile.objects.get_or_create(user=user)
    preferences, _ = UserPreference.objects.get_or_create(user=user)

    # Get user's workspaces
    workspaces = Workspace.objects.filter(owner=user)

    # Get last 10 login attempts
    login_attempts = LoginAttempt.objects.filter(user=user).order_by('-timestamp')[:10]

    # Check account status
    is_locked = LoginAttempt.is_account_locked(user)
    lockout_end_time = LoginAttempt.get_lockout_end_time(user)

    context = {
        'user': user,
        'profile': profile,
        'preferences': preferences,
        'workspaces': workspaces,
        'login_attempts': login_attempts,
        'is_locked': is_locked,
        'lockout_end_time': lockout_end_time,
    }

    return render(request, 'accounts/admin_user_detail.html', context)


# Admin Account Management Actions

@admin_required
@require_http_methods(["POST"])
def admin_unlock_account(request, user_id):
    """
    Admin action to manually unlock a locked user account.
    Resets failed login attempts for the specified user.

    Args:
        request: HTTP request object
        user_id: ID of the user to unlock

    Returns:
        HttpResponse with success message for HTMX
    """
    user = get_object_or_404(User, id=user_id)

    # Reset failed login attempts
    LoginAttempt.reset_failed_attempts(user)

    # Return HTMX-friendly response
    return HttpResponse(
        '<div class="alert alert-success">Account unlocked successfully</div>',
        status=200
    )


@admin_required
@require_http_methods(["POST"])
def admin_trigger_password_reset(request, user_id):
    """
    Admin action to trigger password reset email for a user.
    Uses Django's built-in password reset functionality.

    Args:
        request: HTTP request object
        user_id: ID of the user to send password reset email

    Returns:
        HttpResponse with success message for HTMX
    """
    user = get_object_or_404(User, id=user_id)

    # Create password reset form and send email
    form = PasswordResetForm({'email': user.email})
    if form.is_valid():
        form.save(
            request=request,
            use_https=request.is_secure(),
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
        )

    # Return HTMX-friendly response
    return HttpResponse(
        f'<div class="alert alert-success">Password reset email sent to {user.email}</div>',
        status=200
    )


@admin_required
@require_http_methods(["DELETE"])
def admin_delete_user(request, user_id):
    """
    Admin action to delete a user account.
    Performs cascade delete of associated data:
    - UserProfile
    - UserPreference
    - Workspace
    - LoginAttempts

    Args:
        request: HTTP request object
        user_id: ID of the user to delete

    Returns:
        HttpResponse with redirect for HTMX
    """
    user = get_object_or_404(User, id=user_id)

    # Store email for success message
    user_email = user.email

    # Delete user (cascade deletes related objects automatically)
    user.delete()

    # Return HTMX-friendly response with redirect
    return HttpResponse(
        f'<div class="alert alert-success">User {user_email} deleted successfully</div>',
        status=200,
        headers={'HX-Redirect': reverse_lazy('accounts:admin_user_list')}
    )


@admin_required
@require_http_methods(["POST"])
def admin_toggle_admin(request, user_id):
    """
    Admin action to grant or revoke admin privileges.
    Toggles the is_staff flag for the specified user.

    Args:
        request: HTTP request object
        user_id: ID of the user to toggle admin privileges

    Returns:
        HttpResponse with success message and updated status for HTMX
    """
    user = get_object_or_404(User, id=user_id)

    # Toggle is_staff flag
    user.is_staff = not user.is_staff
    user.save()

    # Determine message based on new status
    if user.is_staff:
        message = f'Admin privileges granted to {user.email}'
    else:
        message = f'Admin privileges revoked from {user.email}'

    # Return HTMX-friendly response
    return HttpResponse(
        f'<div class="alert alert-success">{message}</div>',
        status=200
    )
