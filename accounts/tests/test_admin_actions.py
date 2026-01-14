"""
Tests for admin account management actions.
"""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from accounts.models import LoginAttempt, UserProfile, UserPreference, Workspace
from datetime import timedelta
from django.utils import timezone


@pytest.mark.django_db
class TestAdminUnlockAccount:
    """Test suite for admin unlock account action."""

    def test_admin_can_unlock_locked_account(self):
        """Test that admin can manually unlock a locked user account."""
        # Create admin user
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )

        # Create regular user
        user = User.objects.create_user(
            username='lockeduser',
            email='locked@example.com',
            password='userpass123'
        )

        # Create 3 failed login attempts to lock the account
        for _ in range(3):
            LoginAttempt.objects.create(
                user=user,
                is_successful=False,
                ip_address='127.0.0.1'
            )

        # Verify account is locked
        assert LoginAttempt.is_account_locked(user) is True

        # Login as admin
        client = Client()
        client.login(username='admin', password='adminpass123')

        # Unlock the account
        response = client.post(
            reverse('accounts:admin_unlock_account', kwargs={'user_id': user.id}),
            HTTP_HX_REQUEST='true'
        )

        assert response.status_code == 200
        assert 'Account unlocked successfully' in response.content.decode()

        # Verify account is no longer locked
        assert LoginAttempt.is_account_locked(user) is False
        assert LoginAttempt.objects.filter(user=user, is_successful=False).count() == 0

    def test_non_admin_cannot_unlock_account(self):
        """Test that non-admin users cannot unlock accounts."""
        # Create non-admin user
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='userpass123',
            is_staff=False
        )

        # Create another user to try to unlock
        locked_user = User.objects.create_user(
            username='locked',
            email='locked@example.com',
            password='userpass123'
        )

        # Login as regular user
        client = Client()
        client.login(username='regular', password='userpass123')

        # Try to unlock account
        response = client.post(
            reverse('accounts:admin_unlock_account', kwargs={'user_id': locked_user.id})
        )

        # Should be forbidden
        assert response.status_code == 403


@pytest.mark.django_db
class TestAdminTriggerPasswordReset:
    """Test suite for admin trigger password reset action."""

    def test_admin_can_trigger_password_reset(self):
        """Test that admin can trigger password reset email for any user."""
        # Create admin user
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )

        # Create regular user
        user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )

        # Login as admin
        client = Client()
        client.login(username='admin', password='adminpass123')

        # Trigger password reset
        response = client.post(
            reverse('accounts:admin_trigger_password_reset', kwargs={'user_id': user.id}),
            HTTP_HX_REQUEST='true'
        )

        assert response.status_code == 200
        assert f'Password reset email sent to {user.email}' in response.content.decode()

    def test_non_admin_cannot_trigger_password_reset(self):
        """Test that non-admin users cannot trigger password resets."""
        # Create non-admin user
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='userpass123',
            is_staff=False
        )

        # Create another user
        target_user = User.objects.create_user(
            username='target',
            email='target@example.com',
            password='userpass123'
        )

        # Login as regular user
        client = Client()
        client.login(username='regular', password='userpass123')

        # Try to trigger password reset
        response = client.post(
            reverse('accounts:admin_trigger_password_reset', kwargs={'user_id': target_user.id})
        )

        # Should be forbidden
        assert response.status_code == 403


@pytest.mark.django_db
class TestAdminDeleteUser:
    """Test suite for admin delete user action."""

    def test_admin_can_delete_user_with_cascade(self):
        """Test that admin can delete user and all associated data cascades."""
        # Create admin user
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )

        # Create user to delete
        user = User.objects.create_user(
            username='todelete',
            email='todelete@example.com',
            password='userpass123'
        )

        # Create associated data
        profile = user.profile  # Auto-created by signal
        preference = user.preference  # Auto-created by signal
        workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=user,
            is_personal=True
        )
        login_attempt = LoginAttempt.objects.create(
            user=user,
            is_successful=True,
            ip_address='127.0.0.1'
        )

        user_id = user.id

        # Login as admin
        client = Client()
        client.login(username='admin', password='adminpass123')

        # Delete the user
        response = client.delete(
            reverse('accounts:admin_delete_user', kwargs={'user_id': user_id}),
            HTTP_HX_REQUEST='true'
        )

        assert response.status_code == 200

        # Verify user and all associated data are deleted
        assert User.objects.filter(id=user_id).exists() is False
        assert UserProfile.objects.filter(user_id=user_id).exists() is False
        assert UserPreference.objects.filter(user_id=user_id).exists() is False
        assert Workspace.objects.filter(owner_id=user_id).exists() is False
        assert LoginAttempt.objects.filter(user_id=user_id).exists() is False

    def test_non_admin_cannot_delete_user(self):
        """Test that non-admin users cannot delete other users."""
        # Create non-admin user
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='userpass123',
            is_staff=False
        )

        # Create another user
        target_user = User.objects.create_user(
            username='target',
            email='target@example.com',
            password='userpass123'
        )

        # Login as regular user
        client = Client()
        client.login(username='regular', password='userpass123')

        # Try to delete user
        response = client.delete(
            reverse('accounts:admin_delete_user', kwargs={'user_id': target_user.id})
        )

        # Should be forbidden
        assert response.status_code == 403


@pytest.mark.django_db
class TestAdminToggleAdminPrivileges:
    """Test suite for admin toggle admin privileges action."""

    def test_admin_can_grant_admin_privileges(self):
        """Test that admin can grant admin privileges to regular users."""
        # Create admin user
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )

        # Create regular user
        user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='userpass123',
            is_staff=False
        )

        assert user.is_staff is False

        # Login as admin
        client = Client()
        client.login(username='admin', password='adminpass123')

        # Grant admin privileges
        response = client.post(
            reverse('accounts:admin_toggle_admin', kwargs={'user_id': user.id}),
            HTTP_HX_REQUEST='true'
        )

        assert response.status_code == 200

        # Refresh user from database
        user.refresh_from_db()
        assert user.is_staff is True
        assert 'Admin privileges granted' in response.content.decode()

    def test_admin_can_revoke_admin_privileges(self):
        """Test that admin can revoke admin privileges from users."""
        # Create admin user
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )

        # Create another admin user
        target_admin = User.objects.create_user(
            username='targetadmin',
            email='targetadmin@example.com',
            password='adminpass123',
            is_staff=True
        )

        assert target_admin.is_staff is True

        # Login as admin
        client = Client()
        client.login(username='admin', password='adminpass123')

        # Revoke admin privileges
        response = client.post(
            reverse('accounts:admin_toggle_admin', kwargs={'user_id': target_admin.id}),
            HTTP_HX_REQUEST='true'
        )

        assert response.status_code == 200

        # Refresh user from database
        target_admin.refresh_from_db()
        assert target_admin.is_staff is False
        assert 'Admin privileges revoked' in response.content.decode()

    def test_non_admin_cannot_toggle_privileges(self):
        """Test that non-admin users cannot toggle admin privileges."""
        # Create non-admin user
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='userpass123',
            is_staff=False
        )

        # Create another user
        target_user = User.objects.create_user(
            username='target',
            email='target@example.com',
            password='userpass123',
            is_staff=False
        )

        # Login as regular user
        client = Client()
        client.login(username='regular', password='userpass123')

        # Try to toggle admin privileges
        response = client.post(
            reverse('accounts:admin_toggle_admin', kwargs={'user_id': target_user.id})
        )

        # Should be forbidden
        assert response.status_code == 403
