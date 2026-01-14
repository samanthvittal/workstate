"""
Signal handlers for automatic model creation and updates.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, UserPreference, Workspace, generate_constellation_name


@receiver(post_save, sender=User)
def create_user_related_models(sender, instance, created, **kwargs):
    """
    Automatically create UserProfile, UserPreference, and Workspace when a new User is created.
    This ensures all necessary related data is created during user registration.
    """
    if created:
        # Create UserProfile
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={'timezone': 'UTC'}
        )

        # Create UserPreference with default settings
        UserPreference.objects.get_or_create(
            user=instance,
            defaults={
                'timezone': 'UTC',
                'date_format': 'MM/DD/YYYY',
                'time_format': '12',
                'week_start_day': 'Sunday',
            }
        )

        # Create personal workspace with constellation name
        # The workspace name can be customized during registration via the view
        if not Workspace.objects.filter(owner=instance, is_personal=True).exists():
            workspace_name = generate_constellation_name()
            Workspace.objects.create(
                owner=instance,
                name=workspace_name,
                is_personal=True
            )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Automatically save the UserProfile when User is saved.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
