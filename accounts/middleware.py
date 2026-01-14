"""
Custom middleware for accounts app.
"""
from django.utils import timezone
import pytz


class TimezoneMiddleware:
    """
    Middleware to activate user's timezone for each request.
    Sets the timezone from UserPreference model for authenticated users.
    Applies to all authenticated requests.
    """

    def __init__(self, get_response):
        """
        Initialize middleware with get_response callable.

        Args:
            get_response: Callable that takes a request and returns a response
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process request and activate user's timezone if authenticated.

        Args:
            request: HttpRequest object

        Returns:
            HttpResponse object
        """
        if request.user.is_authenticated:
            # Try to get user's timezone preference
            try:
                user_timezone = request.user.preferences.timezone
                if user_timezone and user_timezone in pytz.all_timezones:
                    timezone.activate(pytz.timezone(user_timezone))
                else:
                    # Fallback to UTC if invalid timezone
                    timezone.activate(pytz.UTC)
            except AttributeError:
                # User doesn't have preferences, use UTC
                timezone.activate(pytz.UTC)
        else:
            # Use default timezone for anonymous users
            timezone.deactivate()

        response = self.get_response(request)
        return response
