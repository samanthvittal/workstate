"""
Home view that redirects based on authentication status.
"""
from django.shortcuts import redirect


def home_view(request):
    """
    Redirect to dashboard if authenticated, otherwise to login.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('accounts:login')
