"""
Custom decorators for access control.
"""
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import render


def admin_required(view_func):
    """
    Decorator for views that require admin access.
    Checks if user is staff (admin). Non-admin users get 403 Forbidden response.

    Usage:
        @admin_required
        def my_admin_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated and is staff
        if not request.user.is_authenticated:
            return render(request, '403.html', status=403)

        if not request.user.is_staff:
            return render(request, '403.html', status=403)

        return view_func(request, *args, **kwargs)

    return wrapper
