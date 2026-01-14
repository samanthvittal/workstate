#!/usr/bin/env python
"""
Script to check and fix user accounts in the database.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workstate.settings')
django.setup()

from django.contrib.auth.models import User
from allauth.account.models import EmailAddress
from accounts.models import UserProfile, UserPreference, Workspace

print("=== Current Users in Database ===")
users = User.objects.all()
if not users:
    print("No users found in database")
else:
    for user in users:
        print(f"\nUser: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Is Active: {user.is_active}")
        print(f"  Is Staff: {user.is_staff}")
        print(f"  Is Superuser: {user.is_superuser}")

        # Check EmailAddress
        email_addresses = EmailAddress.objects.filter(user=user)
        if email_addresses:
            for ea in email_addresses:
                print(f"  EmailAddress: {ea.email} (verified={ea.verified}, primary={ea.primary})")
        else:
            print("  No EmailAddress found")

        # Check Profile
        try:
            profile = user.profile
            print(f"  Has UserProfile: Yes")
        except:
            print(f"  Has UserProfile: No")

        # Check Preferences
        try:
            prefs = user.preferences
            print(f"  Has UserPreference: Yes")
        except:
            print(f"  Has UserPreference: No")

        # Check Workspace
        workspaces = Workspace.objects.filter(owner=user)
        print(f"  Workspaces: {workspaces.count()}")

print("\n=== Actions ===")
print("To activate a user account:")
print("  User.objects.filter(email='user@example.com').update(is_active=True)")
print("\nTo verify email:")
print("  ea = EmailAddress.objects.get(email='user@example.com')")
print("  ea.verified = True")
print("  ea.save()")
