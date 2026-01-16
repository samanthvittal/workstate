"""
Custom template filters for time tracking display.

Provides filters for formatting durations, calculating revenue, and
other time-related display helpers.
"""
from django import template
from datetime import timedelta
from decimal import Decimal

register = template.Library()


@register.filter
def duration_format(duration):
    """
    Format timedelta as human-readable duration string.

    Args:
        duration: timedelta object

    Returns:
        str: Formatted duration (e.g., "2h 30m", "45m", "1h 0m")
    """
    if not duration:
        return "0m"

    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if hours > 0:
        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours}h 0m"
    return f"{minutes}m"


@register.filter
def format_duration(duration):
    """
    Alias for duration_format for template compatibility.

    Args:
        duration: timedelta object

    Returns:
        str: Formatted duration
    """
    return duration_format(duration)


@register.filter
def duration_decimal(duration):
    """
    Convert timedelta to decimal hours for calculations.

    Args:
        duration: timedelta object

    Returns:
        Decimal: Duration in decimal hours (e.g., 2.5 for 2h 30m)
    """
    if not duration:
        return Decimal('0.00')

    total_hours = duration.total_seconds() / 3600
    return Decimal(str(round(total_hours, 2)))


@register.filter
def calculate_revenue(duration, rate):
    """
    Calculate revenue from duration and billable rate.

    Args:
        duration: timedelta object
        rate: Decimal hourly rate

    Returns:
        Decimal: Calculated revenue (duration in hours * rate)
    """
    if not duration or not rate:
        return Decimal('0.00')

    hours = duration_decimal(duration)
    return hours * Decimal(str(rate))


@register.filter
def format_currency(amount, currency='USD'):
    """
    Format monetary amount with currency symbol.

    Args:
        amount: Decimal amount
        currency: Currency code (USD, EUR, GBP, etc.)

    Returns:
        str: Formatted currency string (e.g., "$50.00", "€45.00")
    """
    if not amount:
        amount = Decimal('0.00')

    # Currency symbols mapping
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥',
        'CAD': 'C$',
        'AUD': 'A$',
    }

    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:.2f}"


@register.filter
def sum_durations(entries):
    """
    Sum durations from a list of time entries.

    Args:
        entries: QuerySet or list of TimeEntry objects

    Returns:
        timedelta: Total duration
    """
    total = timedelta(0)
    for entry in entries:
        if entry.duration:
            total += entry.duration
    return total


@register.filter
def sum_revenue(entries):
    """
    Sum revenue from a list of billable time entries.

    Args:
        entries: QuerySet or list of TimeEntry objects

    Returns:
        Decimal: Total revenue
    """
    total = Decimal('0.00')
    for entry in entries:
        if entry.is_billable and entry.duration and entry.billable_rate:
            hours = duration_decimal(entry.duration)
            total += hours * Decimal(str(entry.billable_rate))
    return total
