"""
Admin views for user management dashboard.
"""
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import PasswordResetForm
from django.http import HttpResponse
from django.urls import reverse_lazy

from .models import UserProfile, UserPreference, Workspace, LoginAttempt
from .decorators import admin_required


@admin_required
@require_http_methods(["GET"])
def admin_user_list(request):
    """
    Admin view to display all users with pagination, search, and filtering.

    Features:
    - Display all users with name, email, registration date, account status
    - Pagination (25 users per page)
    - Search by name or email
    - Filter by status (all, active, locked, unverified)
    """
    # Get all users
    users = User.objects.select_related('profile').all().order_by('-date_joined')

    # Search functionality
    search_query = request.GET.get('search', '').strip()
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
        # Get locked users by checking LoginAttempt
        locked_user_ids = []
        for user in users:
            if LoginAttempt.is_account_locked(user):
                locked_user_ids.append(user.pk)
        users = users.filter(pk__in=locked_user_ids)
    elif status_filter == 'unverified':
        # Unverified users have is_active=False
        users = users.filter(is_active=False)

    # Pagination (25 users per page)
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Add account status to each user in the page
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
    Admin view to display detailed information about a specific user.

    Displays:
    - Full user profile information
    - User preferences
    - Workspace information
    - Login history (last 10 attempts)
    """
    user = get_object_or_404(User.objects.select_related('profile'), pk=pk)

    # Get user profile (create if doesn't exist)
    profile, created = UserProfile.objects.get_or_create(user=user)

    # Get user preferences (create if doesn't exist)
    preferences, _ = UserPreference.objects.get_or_create(user=user)

    # Get user workspaces
    workspaces = Workspace.objects.filter(owner=user).order_by('-created_at')

    # Get login history (last 10 attempts)
    login_attempts = LoginAttempt.objects.filter(user=user).order_by('-timestamp')[:10]

    # Check if account is locked
    is_locked = LoginAttempt.is_account_locked(user)
    lockout_end_time = LoginAttempt.get_lockout_end_time(user) if is_locked else None

    context = {
        'object': user,
        'user': user,
        'profile': profile,
        'preferences': preferences,
        'workspaces': workspaces,
        'login_attempts': login_attempts,
        'is_locked': is_locked,
        'lockout_end_time': lockout_end_time,
    }

    return render(request, 'accounts/admin_user_detail.html', context)


@admin_required
@require_http_methods(["POST"])
def admin_unlock_account(request, user_id):
    """
    Admin action to manually unlock a locked user account.
    Resets failed login attempts for the specified user.
    """
    user = get_object_or_404(User, id=user_id)

    # Record a successful login attempt to unlock the account
    LoginAttempt.objects.create(
        user=user,
        is_successful=True,
        ip_address=request.META.get('REMOTE_ADDR', '')
    )

    # Return HTMX-friendly response
    return HttpResponse(
        '<div class="bg-green-50 border border-green-200 text-green-800 px-4 py-2 rounded-lg">Account unlocked successfully</div>',
        status=200
    )


@admin_required
@require_http_methods(["POST"])
def admin_trigger_password_reset(request, user_id):
    """
    Admin action to trigger password reset email for a user.
    Uses Django's built-in password reset functionality.
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
        f'<div class="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-2 rounded-lg">Password reset email sent to {user.email}</div>',
        status=200
    )


@admin_required
@require_http_methods(["POST"])
def admin_delete_user(request, user_id):
    """
    Admin action to delete a user account.
    Performs cascade delete of associated data.
    """
    user = get_object_or_404(User, id=user_id)
    user_email = user.email

    # Delete user (cascade deletes related objects automatically)
    user.delete()

    # Return HTMX-friendly response with redirect
    return HttpResponse(
        status=200,
        headers={'HX-Redirect': reverse_lazy('accounts:admin_user_list')}
    )


@admin_required
@require_http_methods(["POST"])
def admin_toggle_admin(request, user_id):
    """
    Admin action to grant or revoke admin privileges.
    Toggles the is_staff flag for the specified user.
    """
    user = get_object_or_404(User, id=user_id)

    # Toggle is_staff flag
    user.is_staff = not user.is_staff
    user.save()

    # Determine message and button state
    if user.is_staff:
        message = f'Admin privileges granted to {user.email}'
        button_text = 'Revoke Admin'
        button_class = 'bg-yellow-600 hover:bg-yellow-700'
    else:
        message = f'Admin privileges revoked from {user.email}'
        button_text = 'Grant Admin'
        button_class = 'bg-blue-600 hover:bg-blue-700'

    # Return HTMX-friendly response with updated button
    return HttpResponse(
        f'<div hx-swap-oob="true" id="admin-toggle-btn">'
        f'<button hx-post="/accounts/admin-dashboard/users/{user.id}/toggle-admin/" '
        f'hx-target="#admin-action-result" '
        f'class="{button_class} text-white px-4 py-2 rounded-lg font-medium">{button_text}</button>'
        f'</div>'
        f'<div class="bg-green-50 border border-green-200 text-green-800 px-4 py-2 rounded-lg">{message}</div>',
        status=200
    )
