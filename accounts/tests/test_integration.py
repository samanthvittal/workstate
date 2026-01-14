"""
Integration tests for user authentication and workspace setup feature.

These tests cover critical end-to-end workflows that integrate multiple layers
(database, backend, frontend) to ensure the complete feature works as expected.
"""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from django.core import mail
from django.utils import timezone
from datetime import timedelta, datetime, date, time as dt_time
from allauth.account.models import EmailAddress
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import (
    UserProfile, UserPreference, Workspace, LoginAttempt
)


@pytest.mark.django_db
class TestEndToEndRegistrationFlow:
    """
    Test complete registration workflow from form submission through
    email verification to workspace creation and first login.
    """

    def test_complete_registration_to_login_workflow(self, client):
        """
        End-to-end: Registration → Email Verification → Workspace Creation → Login.

        Tests the entire user onboarding flow including:
        - Form submission with valid data
        - Email verification email sent
        - User, UserProfile, UserPreference, and Workspace creation
        - Email confirmation
        - Successful first login
        """
        # Step 1: Submit registration form
        registration_data = {
            'email': 'newuser@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'full_name': 'New User',
            'workspace_name': 'My Personal Space',
            'job_title': 'Software Engineer',
            'company': 'Tech Corp',
        }

        response = client.post(reverse('accounts:register'), registration_data)
        assert response.status_code == 302  # Redirect to verification page

        # Step 2: Verify all models were created
        user = User.objects.get(email='newuser@example.com')
        assert user is not None
        assert not user.is_active  # Not active until email verification

        # Verify UserProfile created with correct data
        assert hasattr(user, 'profile')
        assert user.profile.full_name == 'New User'
        assert user.profile.job_title == 'Software Engineer'
        assert user.profile.company == 'Tech Corp'

        # Verify UserPreference created with defaults
        assert hasattr(user, 'preferences')
        assert user.preferences.timezone == 'UTC'
        assert user.preferences.date_format == 'MM/DD/YYYY'
        assert user.preferences.time_format == '12'

        # Verify Workspace created with custom name
        workspace = Workspace.objects.get(owner=user)
        assert workspace.name == 'My Personal Space'
        assert workspace.is_personal is True

        # Step 3: Verify email was sent
        assert len(mail.outbox) == 1
        assert 'newuser@example.com' in mail.outbox[0].to

        # Step 4: Simulate email verification
        email_address = EmailAddress.objects.get(email='newuser@example.com')
        email_address.verified = True
        email_address.save()
        user.is_active = True
        user.save()

        # Step 5: Login with verified account
        login_response = client.post(reverse('accounts:login'), {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
        })

        assert login_response.status_code == 302  # Successful login redirect

        # Verify successful login attempt was recorded
        login_attempt = LoginAttempt.objects.filter(
            user=user,
            is_successful=True
        ).first()
        assert login_attempt is not None


@pytest.mark.django_db
class TestEndToEndLoginLockoutFlow:
    """
    Test complete login lockout workflow: failed attempts → lockout →
    auto-unlock → successful login.
    """

    def test_complete_lockout_and_auto_unlock_workflow(self, client):
        """
        End-to-end: 3 Failed Attempts → Lockout → 30min Wait → Successful Login.

        Tests the account security flow including:
        - Three consecutive failed login attempts
        - Account lockout triggered
        - Lockout message displayed
        - Auto-unlock after 30 minutes
        - Successful login after unlock
        """
        # Setup: Create verified user
        user = User.objects.create_user(
            username='locktest@example.com',
            email='locktest@example.com',
            password='CorrectPass123!',
            is_active=True
        )

        # Step 1: Three failed login attempts
        for i in range(3):
            response = client.post(reverse('accounts:login'), {
                'email': 'locktest@example.com',
                'password': f'WrongPassword{i}',
            })
            assert response.status_code == 200  # Stays on login page

        # Step 2: Verify account is locked
        assert LoginAttempt.is_account_locked(user) is True

        # Step 3: Attempt login with correct password (should be blocked)
        response = client.post(reverse('accounts:login'), {
            'email': 'locktest@example.com',
            'password': 'CorrectPass123!',
        })
        assert response.status_code == 200
        assert b'locked' in response.content.lower()
        assert b'30' in response.content  # 30 minute wait message

        # Step 4: Simulate 31 minutes passing
        past_time = timezone.now() - timedelta(minutes=31)
        LoginAttempt.objects.filter(user=user).update(timestamp=past_time)

        # Step 5: Verify account auto-unlocked
        assert LoginAttempt.is_account_locked(user) is False

        # Step 6: Successful login after auto-unlock
        response = client.post(reverse('accounts:login'), {
            'email': 'locktest@example.com',
            'password': 'CorrectPass123!',
        })
        assert response.status_code == 302  # Successful login redirect

        # Verify successful login attempt recorded
        successful_attempt = LoginAttempt.objects.filter(
            user=user,
            is_successful=True
        ).exists()
        assert successful_attempt is True


@pytest.mark.django_db
class TestEndToEndPasswordResetFlow:
    """
    Test complete password reset workflow from request through email
    to password change and login.
    """

    def test_complete_password_reset_workflow(self, client):
        """
        End-to-end: Request → Email → Token Validation → New Password → Login.

        Tests the password reset flow including:
        - Password reset request
        - Reset email sent with token
        - Token validation
        - New password set
        - Login with new password
        """
        # Setup: Create verified user
        user = User.objects.create_user(
            username='resettest@example.com',
            email='resettest@example.com',
            password='OldPassword123!',
            is_active=True
        )

        # Step 1: Request password reset
        response = client.post(reverse('accounts:password_reset'), {
            'email': 'resettest@example.com',
        })
        assert response.status_code in [200, 302]

        # Step 2: Verify reset email was sent
        assert len(mail.outbox) >= 1
        reset_email = [email for email in mail.outbox if 'resettest@example.com' in email.to]
        assert len(reset_email) > 0

        # Step 3: Extract token from email (simulated)
        # In real flow, user clicks link in email
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Step 4: Access password reset confirm page
        reset_url = reverse('accounts:password_reset_confirm', kwargs={
            'uidb64': uid,
            'token': token
        })
        response = client.get(reset_url)
        assert response.status_code in [200, 302]

        # Step 5: Set new password
        response = client.post(reset_url, {
            'new_password1': 'NewSecurePass456!',
            'new_password2': 'NewSecurePass456!',
        }, follow=True)

        # Step 6: Verify old password no longer works
        login_old = client.post(reverse('accounts:login'), {
            'email': 'resettest@example.com',
            'password': 'OldPassword123!',
        })
        # Should fail or redirect back to login
        assert not client.session.get('_auth_user_id')

        # Step 7: Login with new password
        client.logout()
        login_new = client.post(reverse('accounts:login'), {
            'email': 'resettest@example.com',
            'password': 'NewSecurePass456!',
        })
        assert login_new.status_code == 302  # Successful login


@pytest.mark.django_db
class TestEndToEndProfileUpdateFlow:
    """
    Test complete profile update workflow including avatar upload.
    """

    def test_complete_profile_update_with_avatar_workflow(self, client):
        """
        End-to-end: Edit Profile → Avatar Upload → Save → Verify Display.

        Tests the profile management flow including:
        - Load profile data
        - Update profile fields
        - Upload avatar image
        - Save changes
        - Verify updated data displays correctly
        """
        # Setup: Create and login user
        user = User.objects.create_user(
            username='profiletest@example.com',
            email='profiletest@example.com',
            password='TestPass123!',
            is_active=True
        )
        UserProfile.objects.create(
            user=user,
            full_name='Old Name',
            job_title='Junior Dev',
        )

        client.login(username='profiletest@example.com', password='TestPass123!')

        # Step 1: Access profile page
        response = client.get(reverse('accounts:profile'))
        assert response.status_code == 200
        assert b'Old Name' in response.content

        # Step 2: Create avatar image
        image = Image.new('RGB', (200, 200), color='blue')
        image_file = BytesIO()
        image.save(image_file, 'PNG')
        image_file.seek(0)

        avatar = SimpleUploadedFile(
            'new_avatar.png',
            image_file.read(),
            content_type='image/png'
        )

        # Step 3: Update profile with new data and avatar
        update_response = client.post(reverse('accounts:profile_edit'), {
            'full_name': 'Updated Name',
            'job_title': 'Senior Developer',
            'company': 'New Company Inc',
            'phone_number': '+1-555-0123',
            'timezone': 'America/New_York',
            'avatar': avatar,
        })

        assert update_response.status_code == 302  # Redirect after save

        # Step 4: Verify data was saved
        user.refresh_from_db()
        profile = user.profile
        assert profile.full_name == 'Updated Name'
        assert profile.job_title == 'Senior Developer'
        assert profile.company == 'New Company Inc'
        assert profile.phone_number == '+1-555-0123'
        assert profile.timezone == 'America/New_York'
        assert profile.avatar
        assert 'avatars/' in profile.avatar.name

        # Step 5: Verify updated data displays on profile page
        response = client.get(reverse('accounts:profile'))
        assert response.status_code == 200
        assert b'Updated Name' in response.content
        assert b'Senior Developer' in response.content

        # Cleanup
        if profile.avatar:
            profile.avatar.delete()


@pytest.mark.django_db
class TestEndToEndPreferencesFlow:
    """
    Test complete preferences workflow including timezone auto-detection
    and format application.
    """

    def test_complete_preferences_update_and_display_workflow(self, client):
        """
        End-to-end: Timezone Auto-detect → Update Preferences → Verify Format Application.

        Tests the preferences flow including:
        - Timezone detection
        - Update all preference fields
        - Verify date/time format applied in templates
        """
        # Setup: Create and login user
        user = User.objects.create_user(
            username='preftest@example.com',
            email='preftest@example.com',
            password='TestPass123!',
            is_active=True
        )
        UserPreference.objects.create(user=user)

        client.login(username='preftest@example.com', password='TestPass123!')

        # Step 1: Access preferences page
        response = client.get(reverse('accounts:preferences'))
        assert response.status_code == 200

        # Step 2: Update preferences (simulating browser timezone detection)
        update_response = client.post(reverse('accounts:preferences_edit'), {
            'timezone': 'Europe/London',
            'date_format': 'DD/MM/YYYY',
            'time_format': '24',
            'week_start_day': 'Monday',
        })

        assert update_response.status_code in [200, 302]

        # Step 3: Verify preferences saved
        user.refresh_from_db()
        prefs = user.preferences
        assert prefs.timezone == 'Europe/London'
        assert prefs.date_format == 'DD/MM/YYYY'
        assert prefs.time_format == '24'
        assert prefs.week_start_day == 'Monday'

        # Step 4: Verify format application using template filters
        from accounts.templatetags.preference_filters import user_date, user_time

        test_date = date(2024, 3, 15)
        formatted_date = user_date(test_date, user)
        assert formatted_date == '15/03/2024'  # DD/MM/YYYY format

        test_time = dt_time(14, 30, 0)
        formatted_time = user_time(test_time, user)
        assert '14:30' in formatted_time  # 24-hour format
        assert 'PM' not in formatted_time


@pytest.mark.django_db
class TestEndToEndAdminUnlockFlow:
    """
    Test complete admin unlock workflow for locked user accounts.
    """

    def test_complete_admin_unlock_user_workflow(self, client):
        """
        End-to-end: User Locked → Admin Unlocks → User Can Login.

        Tests the admin unlock flow including:
        - User account locked after failed attempts
        - Admin manually unlocks account
        - User can immediately login
        """
        # Setup: Create admin and locked user
        admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_active=True
        )

        locked_user = User.objects.create_user(
            username='locked@example.com',
            email='locked@example.com',
            password='UserPass123!',
            is_active=True
        )

        # Step 1: Lock user account with 3 failed attempts
        for _ in range(3):
            LoginAttempt.objects.create(
                user=locked_user,
                is_successful=False,
                ip_address='192.168.1.100'
            )

        assert LoginAttempt.is_account_locked(locked_user) is True

        # Step 2: Verify locked user cannot login
        client.post(reverse('accounts:login'), {
            'email': 'locked@example.com',
            'password': 'UserPass123!',
        })
        # User should still be locked
        assert LoginAttempt.is_account_locked(locked_user) is True

        # Step 3: Admin logs in and unlocks account
        client.login(username='admin@example.com', password='AdminPass123!')

        unlock_response = client.post(
            reverse('accounts:admin_unlock_account', kwargs={'user_id': locked_user.id}),
            HTTP_HX_REQUEST='true'
        )

        assert unlock_response.status_code == 200
        assert b'Account unlocked successfully' in unlock_response.content

        # Step 4: Verify account is unlocked
        assert LoginAttempt.is_account_locked(locked_user) is False

        # Step 5: User can now login immediately
        client.logout()
        login_response = client.post(reverse('accounts:login'), {
            'email': 'locked@example.com',
            'password': 'UserPass123!',
        })

        assert login_response.status_code == 302  # Successful login


@pytest.mark.django_db
class TestEndToEndAdminDeleteFlow:
    """
    Test complete admin delete user workflow with cascade verification.
    """

    def test_complete_admin_delete_user_cascade_workflow(self, client):
        """
        End-to-end: Admin Deletes User → Cascade Delete Verified.

        Tests the admin delete flow including:
        - User has profile, preferences, workspace, login attempts
        - Admin deletes user
        - All associated data cascade deleted
        """
        # Setup: Create admin
        admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_active=True
        )

        # Setup: Create user with all associated data
        user_to_delete = User.objects.create_user(
            username='todelete@example.com',
            email='todelete@example.com',
            password='DeleteMe123!',
            is_active=True
        )

        # Create associated models (auto-created by signals)
        profile = user_to_delete.profile
        preference = user_to_delete.preferences

        # Create workspace
        workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=user_to_delete,
            is_personal=True
        )

        # Create login attempts
        LoginAttempt.objects.create(
            user=user_to_delete,
            is_successful=True,
            ip_address='127.0.0.1'
        )

        user_id = user_to_delete.id

        # Verify all data exists
        assert User.objects.filter(id=user_id).exists()
        assert UserProfile.objects.filter(user_id=user_id).exists()
        assert UserPreference.objects.filter(user_id=user_id).exists()
        assert Workspace.objects.filter(owner_id=user_id).exists()
        assert LoginAttempt.objects.filter(user_id=user_id).exists()

        # Step 1: Admin logs in
        client.login(username='admin@example.com', password='AdminPass123!')

        # Step 2: Admin deletes user
        delete_response = client.delete(
            reverse('accounts:admin_delete_user', kwargs={'user_id': user_id}),
            HTTP_HX_REQUEST='true'
        )

        assert delete_response.status_code == 200

        # Step 3: Verify user deleted
        assert not User.objects.filter(id=user_id).exists()

        # Step 4: Verify all associated data cascade deleted
        assert not UserProfile.objects.filter(user_id=user_id).exists()
        assert not UserPreference.objects.filter(user_id=user_id).exists()
        assert not Workspace.objects.filter(owner_id=user_id).exists()
        assert not LoginAttempt.objects.filter(user_id=user_id).exists()


@pytest.mark.django_db
class TestIntegrationRegistrationCreatesAllModels:
    """
    Integration test verifying registration creates all required models together.
    """

    def test_registration_creates_user_profile_preference_workspace(self, client):
        """
        Integration: Registration Creates All Related Models.

        Verifies that a single registration action properly creates:
        - User model
        - UserProfile model
        - UserPreference model
        - Workspace model

        All with correct relationships and default values.
        """
        # Register new user
        registration_data = {
            'email': 'integration@example.com',
            'password1': 'IntegrationTest123!',
            'password2': 'IntegrationTest123!',
            'full_name': 'Integration Test User',
        }

        response = client.post(reverse('accounts:register'), registration_data)
        assert response.status_code == 302

        # Verify User created
        user = User.objects.get(email='integration@example.com')
        assert user is not None

        # Verify UserProfile created and linked
        assert hasattr(user, 'profile')
        profile = user.profile
        assert profile.user == user
        assert profile.full_name == 'Integration Test User'
        assert profile.timezone == 'UTC'

        # Verify UserPreference created and linked
        assert hasattr(user, 'preferences')
        preference = user.preferences
        assert preference.user == user
        assert preference.timezone == 'UTC'
        assert preference.date_format == 'MM/DD/YYYY'
        assert preference.time_format == '12'
        assert preference.week_start_day == 'Sunday'

        # Verify Workspace created and linked
        workspace = Workspace.objects.get(owner=user)
        assert workspace.owner == user
        assert workspace.is_personal is True
        # Should have constellation name since no workspace_name provided
        constellation_names = [
            'Orion', 'Andromeda', 'Cassiopeia', 'Lyra', 'Cygnus',
            'Perseus', 'Draco', 'Ursa Major', 'Phoenix', 'Centaurus'
        ]
        assert workspace.name in constellation_names


@pytest.mark.django_db
class TestIntegrationTimezonePreferenceAffectsDisplay:
    """
    Integration test verifying timezone preference affects datetime display
    throughout the application.
    """

    def test_timezone_preference_affects_datetime_display(self, client):
        """
        Integration: Timezone Preference Affects Datetime Display Across App.

        Verifies that user's timezone preference is applied to:
        - Date formatting via template filters
        - Time formatting via template filters
        - Datetime display consistency
        """
        # Setup: Create user with specific timezone
        user = User.objects.create_user(
            username='tztest@example.com',
            email='tztest@example.com',
            password='TestPass123!',
            is_active=True
        )

        # Create preference with specific timezone and formats
        UserPreference.objects.create(
            user=user,
            timezone='America/Los_Angeles',
            date_format='YYYY-MM-DD',
            time_format='24',
            week_start_day='Monday'
        )

        # Test template filters apply preference
        from accounts.templatetags.preference_filters import user_date, user_time, user_datetime

        # Test date formatting
        test_date = date(2024, 12, 25)
        formatted_date = user_date(test_date, user)
        assert formatted_date == '2024-12-25'

        # Test time formatting
        test_time = dt_time(15, 45, 30)
        formatted_time = user_time(test_time, user)
        assert '15:45' in formatted_time

        # Test datetime formatting
        test_datetime = datetime(2024, 12, 25, 15, 45, 30)
        formatted_datetime = user_datetime(test_datetime, user)
        assert '2024-12-25' in formatted_datetime
        assert '15:45' in formatted_datetime


@pytest.mark.django_db
class TestIntegrationAdminPermissionChecks:
    """
    Integration test verifying admin permission checks prevent
    non-admin access to sensitive operations.
    """

    def test_admin_permission_checks_prevent_non_admin_access(self, client):
        """
        Integration: Admin Permission Checks Prevent Non-Admin Access.

        Verifies that all admin-only endpoints properly check permissions:
        - Admin user list
        - Admin user detail
        - Unlock account
        - Trigger password reset
        - Delete user
        - Toggle admin privileges
        """
        # Setup: Create admin and regular user
        admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_active=True
        )

        regular_user = User.objects.create_user(
            username='regular@example.com',
            email='regular@example.com',
            password='RegularPass123!',
            is_staff=False,
            is_active=True
        )

        target_user = User.objects.create_user(
            username='target@example.com',
            email='target@example.com',
            password='TargetPass123!',
            is_active=True
        )

        # Login as regular user
        client.login(username='regular@example.com', password='RegularPass123!')

        # Test all admin endpoints return 403 Forbidden
        endpoints = [
            ('accounts:admin_user_list', {}),
            ('accounts:admin_user_detail', {'pk': target_user.id}),
            ('accounts:admin_unlock_account', {'user_id': target_user.id}),
            ('accounts:admin_trigger_password_reset', {'user_id': target_user.id}),
            ('accounts:admin_delete_user', {'user_id': target_user.id}),
            ('accounts:admin_toggle_admin', {'user_id': target_user.id}),
        ]

        for url_name, kwargs in endpoints:
            response = client.get(reverse(url_name, kwargs=kwargs))
            assert response.status_code == 403, f"Failed permission check for {url_name}"

        # Logout and login as admin
        client.logout()
        client.login(username='admin@example.com', password='AdminPass123!')

        # Verify admin can access endpoints
        for url_name, kwargs in endpoints:
            response = client.get(reverse(url_name, kwargs=kwargs))
            # Admin should get 200 or 405 (Method Not Allowed for POST-only endpoints)
            assert response.status_code in [200, 405], f"Admin blocked from {url_name}"
