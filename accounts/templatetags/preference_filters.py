"""
Template filters for formatting dates and times according to user preferences.
"""
from django import template
from django.utils import timezone as django_timezone
import pytz
from datetime import datetime, date, time

register = template.Library()


@register.filter(name='user_date')
def user_date(value, user):
    """
    Format a date according to the user's date format preference.

    Args:
        value: datetime.date or datetime.datetime object
        user: User object with preferences

    Returns:
        Formatted date string according to user's preference
    """
    if not value:
        return ''

    if not user or not hasattr(user, 'preferences'):
        # Default to MM/DD/YYYY if no preferences
        if isinstance(value, datetime):
            return value.strftime('%m/%d/%Y')
        elif isinstance(value, date):
            return value.strftime('%m/%d/%Y')
        return str(value)

    try:
        preferences = user.preferences
        date_format = preferences.date_format

        # Extract date if datetime object
        if isinstance(value, datetime):
            date_obj = value.date()
        else:
            date_obj = value

        # Format according to preference
        if date_format == 'MM/DD/YYYY':
            return date_obj.strftime('%m/%d/%Y')
        elif date_format == 'DD/MM/YYYY':
            return date_obj.strftime('%d/%m/%Y')
        elif date_format == 'YYYY-MM-DD':
            return date_obj.strftime('%Y-%m-%d')
        else:
            # Fallback to MM/DD/YYYY
            return date_obj.strftime('%m/%d/%Y')

    except Exception:
        # Fallback to default format
        if isinstance(value, datetime):
            return value.strftime('%m/%d/%Y')
        elif isinstance(value, date):
            return value.strftime('%m/%d/%Y')
        return str(value)


@register.filter(name='user_time')
def user_time(value, user):
    """
    Format a time according to the user's time format preference.

    Args:
        value: datetime.time or datetime.datetime object
        user: User object with preferences

    Returns:
        Formatted time string according to user's preference
    """
    if not value:
        return ''

    if not user or not hasattr(user, 'preferences'):
        # Default to 12-hour format
        if isinstance(value, datetime):
            return value.strftime('%I:%M %p')
        elif isinstance(value, time):
            return value.strftime('%I:%M %p')
        return str(value)

    try:
        preferences = user.preferences
        time_format = preferences.time_format

        # Extract time if datetime object
        if isinstance(value, datetime):
            time_obj = value.time()
        else:
            time_obj = value

        # Format according to preference
        if time_format == '24':
            return time_obj.strftime('%H:%M')
        else:  # Default to 12-hour
            return time_obj.strftime('%I:%M %p')

    except Exception:
        # Fallback to 12-hour format
        if isinstance(value, datetime):
            return value.strftime('%I:%M %p')
        elif isinstance(value, time):
            return value.strftime('%I:%M %p')
        return str(value)


@register.filter(name='user_datetime')
def user_datetime(value, user):
    """
    Format a datetime according to the user's date and time format preferences.
    Also applies the user's timezone.

    Args:
        value: datetime.datetime object
        user: User object with preferences

    Returns:
        Formatted datetime string according to user's preferences
    """
    if not value:
        return ''

    if not isinstance(value, datetime):
        return str(value)

    # Apply user's timezone if available
    if user and hasattr(user, 'preferences'):
        try:
            preferences = user.preferences
            user_tz = pytz.timezone(preferences.timezone)

            # Convert to user's timezone if value is timezone-aware
            if django_timezone.is_aware(value):
                value = value.astimezone(user_tz)
            else:
                # Make aware in UTC first, then convert
                value = django_timezone.make_aware(value, pytz.UTC)
                value = value.astimezone(user_tz)

        except Exception:
            pass  # Use value as-is if timezone conversion fails

    # Format date and time parts
    date_part = user_date(value, user)
    time_part = user_time(value, user)

    return f"{date_part} {time_part}"


@register.filter(name='user_timezone')
def user_timezone(value, user):
    """
    Convert a datetime to the user's timezone without formatting.

    Args:
        value: datetime.datetime object
        user: User object with preferences

    Returns:
        datetime object in user's timezone
    """
    if not value or not isinstance(value, datetime):
        return value

    if not user or not hasattr(user, 'preferences'):
        return value

    try:
        preferences = user.preferences
        user_tz = pytz.timezone(preferences.timezone)

        # Convert to user's timezone
        if django_timezone.is_aware(value):
            return value.astimezone(user_tz)
        else:
            # Make aware in UTC first, then convert
            value = django_timezone.make_aware(value, pytz.UTC)
            return value.astimezone(user_tz)

    except Exception:
        return value
