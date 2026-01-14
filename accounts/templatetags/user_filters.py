"""
Custom template filters for user display.
"""
from django import template
import hashlib

register = template.Library()


@register.filter
def first_name(user):
    """
    Get the first name of a user.
    Returns the first word of full_name if available,
    otherwise the part before @ in email.
    """
    if hasattr(user, 'profile') and user.profile.full_name:
        return user.profile.full_name.split()[0]
    elif user.email:
        return user.email.split('@')[0].capitalize()
    return "User"


@register.filter
def get_initials(user):
    """
    Get user initials for avatar display.
    Returns first letter of first and last name if available,
    otherwise first two letters of username/email.
    """
    if hasattr(user, 'profile') and user.profile.full_name:
        parts = user.profile.full_name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        return parts[0][:2].upper()
    elif user.first_name and user.last_name:
        return f"{user.first_name[0]}{user.last_name[0]}".upper()
    elif user.email:
        name = user.email.split('@')[0]
        return name[:2].upper()
    return "U"


@register.filter
def get_user_color(user):
    """
    Generate a consistent color for user avatar based on user ID.
    Uses hash of user ID to generate a color from a predefined palette.
    """
    colors = [
        '#3B82F6',  # blue
        '#8B5CF6',  # purple
        '#EC4899',  # pink
        '#F59E0B',  # amber
        '#10B981',  # green
        '#06B6D4',  # cyan
        '#EF4444',  # red
        '#6366F1',  # indigo
        '#14B8A6',  # teal
        '#F97316',  # orange
    ]

    # Use hash of user ID to consistently select a color
    hash_value = int(hashlib.md5(str(user.id).encode()).hexdigest(), 16)
    return colors[hash_value % len(colors)]
