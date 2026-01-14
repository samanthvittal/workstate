#!/usr/bin/env python
"""
Script to create a test user for development.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workstate.settings')
django.setup()

from django.contrib.auth.models import User
from allauth.account.models import EmailAddress
from accounts.models import UserProfile, UserPreference, Workspace, generate_constellation_name

# Test user credentials
email = "test@example.com"
password = "testpass123"
full_name = "Test User"

print("=== Creating Test User ===")

# Check if user exists
if User.objects.filter(email=email).exists():
    print(f"User with email {email} already exists!")
    user = User.objects.get(email=email)
    print(f"Activating existing user...")
    user.is_active = True
    user.save()

    # Verify email if not already verified
    try:
        email_addr = EmailAddress.objects.get(email=email)
        email_addr.verified = True
        email_addr.save()
        print(f"Email verified!")
    except EmailAddress.DoesNotExist:
        EmailAddress.objects.create(
            user=user,
            email=email,
            primary=True,
            verified=True
        )
        print(f"EmailAddress created and verified!")
else:
    # Create new user
    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        is_active=True
    )
    print(f"Created user: {email}")

    # Update profile
    try:
        profile = user.profile
        profile.full_name = full_name
        profile.save()
        print(f"Updated user profile")
    except:
        UserProfile.objects.create(
            user=user,
            full_name=full_name
        )
        print(f"Created user profile")

    # Create preferences if not exists
    if not hasattr(user, 'preferences'):
        UserPreference.objects.create(user=user)
        print(f"Created user preferences")

    # Create workspace if not exists
    if not Workspace.objects.filter(owner=user).exists():
        workspace_name = generate_constellation_name()
        Workspace.objects.create(
            owner=user,
            name=workspace_name,
            is_personal=True
        )
        print(f"Created workspace: {workspace_name}")

    # Create and verify email
    EmailAddress.objects.create(
        user=user,
        email=email,
        primary=True,
        verified=True
    )
    print(f"EmailAddress created and verified!")

print("\n=== Test User Ready! ===")
print(f"Email: {email}")
print(f"Password: {password}")
print(f"Status: Active and Verified")
print(f"\nYou can now log in at: http://localhost:8000/accounts/login/")
