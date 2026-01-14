"""
Tests for UserPreference and LoginAttempt models.
"""
import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserPreference, LoginAttempt


@pytest.mark.django_db
class TestUserPreferenceModel:
    """Tests for UserPreference model."""

    def test_preference_creation_with_defaults(self):
        """Test that UserPreference is created with default values."""
        user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        preference = UserPreference.objects.create(user=user)

        assert preference.user == user
        assert preference.timezone == 'UTC'
        assert preference.date_format == 'MM/DD/YYYY'
        assert preference.time_format == '12'
        assert preference.week_start_day == 'Sunday'
        assert preference.created_at is not None
        assert preference.updated_at is not None

    def test_preference_timezone_options(self):
        """Test that timezone can be set to valid timezone values."""
        user = User.objects.create_user(
            username='testuser2@example.com',
            email='testuser2@example.com',
            password='testpass123'
        )
        preference = UserPreference.objects.create(
            user=user,
            timezone='America/New_York'
        )

        assert preference.timezone == 'America/New_York'

    def test_preference_date_format_options(self):
        """Test all date format choices work correctly."""
        user = User.objects.create_user(
            username='testuser3@example.com',
            email='testuser3@example.com',
            password='testpass123'
        )

        # Test DD/MM/YYYY format
        preference = UserPreference.objects.create(
            user=user,
            date_format='DD/MM/YYYY'
        )
        assert preference.date_format == 'DD/MM/YYYY'

        # Update to YYYY-MM-DD format
        preference.date_format = 'YYYY-MM-DD'
        preference.save()
        preference.refresh_from_db()
        assert preference.date_format == 'YYYY-MM-DD'

    def test_preference_time_format_options(self):
        """Test time format 12-hour and 24-hour options."""
        user = User.objects.create_user(
            username='testuser4@example.com',
            email='testuser4@example.com',
            password='testpass123'
        )
        preference = UserPreference.objects.create(
            user=user,
            time_format='24'
        )

        assert preference.time_format == '24'

    def test_preference_week_start_day_options(self):
        """Test week start day options."""
        user = User.objects.create_user(
            username='testuser5@example.com',
            email='testuser5@example.com',
            password='testpass123'
        )

        # Test Monday start
        preference = UserPreference.objects.create(
            user=user,
            week_start_day='Monday'
        )
        assert preference.week_start_day == 'Monday'

        # Update to Saturday
        preference.week_start_day = 'Saturday'
        preference.save()
        preference.refresh_from_db()
        assert preference.week_start_day == 'Saturday'


@pytest.mark.django_db
class TestLoginAttemptModel:
    """Tests for LoginAttempt model and account lockout logic."""

    def test_failed_login_attempt_tracking(self):
        """Test that failed login attempts are tracked correctly."""
        user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )

        # Record a failed login attempt
        attempt = LoginAttempt.objects.create(
            user=user,
            is_successful=False,
            ip_address='192.168.1.1'
        )

        assert attempt.user == user
        assert attempt.is_successful is False
        assert attempt.ip_address == '192.168.1.1'
        assert attempt.timestamp is not None

    def test_account_lockout_after_three_attempts(self):
        """Test that account is locked after 3 consecutive failed attempts."""
        user = User.objects.create_user(
            username='testuser2@example.com',
            email='testuser2@example.com',
            password='testpass123'
        )

        # Initially account should not be locked
        assert LoginAttempt.is_account_locked(user) is False

        # Create 3 failed login attempts
        for i in range(3):
            LoginAttempt.objects.create(
                user=user,
                is_successful=False,
                ip_address=f'192.168.1.{i}'
            )

        # Account should now be locked
        assert LoginAttempt.is_account_locked(user) is True

    def test_auto_unlock_after_30_minutes(self):
        """Test that account unlocks automatically after 30 minutes."""
        user = User.objects.create_user(
            username='testuser3@example.com',
            email='testuser3@example.com',
            password='testpass123'
        )

        # Create 3 failed attempts 31 minutes ago
        past_time = timezone.now() - timedelta(minutes=31)
        for i in range(3):
            attempt = LoginAttempt.objects.create(
                user=user,
                is_successful=False,
                ip_address=f'192.168.1.{i}'
            )
            # Manually set timestamp to past
            LoginAttempt.objects.filter(pk=attempt.pk).update(timestamp=past_time)

        # Account should not be locked (attempts are too old)
        assert LoginAttempt.is_account_locked(user) is False

    def test_successful_login_resets_lockout(self):
        """Test that successful login after failed attempts unlocks account."""
        user = User.objects.create_user(
            username='testuser4@example.com',
            email='testuser4@example.com',
            password='testpass123'
        )

        # Create 3 failed attempts
        for i in range(3):
            LoginAttempt.objects.create(
                user=user,
                is_successful=False,
                ip_address=f'192.168.1.{i}'
            )

        # Account should be locked
        assert LoginAttempt.is_account_locked(user) is True

        # Record successful login
        LoginAttempt.objects.create(
            user=user,
            is_successful=True,
            ip_address='192.168.1.100'
        )

        # Account should no longer be locked
        assert LoginAttempt.is_account_locked(user) is False

    def test_get_lockout_end_time(self):
        """Test that lockout end time is calculated correctly."""
        user = User.objects.create_user(
            username='testuser5@example.com',
            email='testuser5@example.com',
            password='testpass123'
        )

        # Create 3 failed attempts
        for i in range(3):
            LoginAttempt.objects.create(
                user=user,
                is_successful=False,
                ip_address=f'192.168.1.{i}'
            )

        lockout_end = LoginAttempt.get_lockout_end_time(user)
        assert lockout_end is not None

        # Lockout end time should be approximately 30 minutes from the last attempt
        last_attempt = LoginAttempt.objects.filter(
            user=user,
            is_successful=False
        ).latest('timestamp')
        expected_end = last_attempt.timestamp + timedelta(minutes=30)

        # Allow 1 second difference for test execution time
        time_diff = abs((lockout_end - expected_end).total_seconds())
        assert time_diff < 1

    def test_reset_failed_attempts_method_exists(self):
        """Test that reset_failed_attempts method exists and can be called."""
        user = User.objects.create_user(
            username='testuser6@example.com',
            email='testuser6@example.com',
            password='testpass123'
        )

        # Create some failed attempts
        for i in range(2):
            LoginAttempt.objects.create(
                user=user,
                is_successful=False,
                ip_address=f'192.168.1.{i}'
            )

        # Call reset method (implementation may vary)
        LoginAttempt.reset_failed_attempts(user)

        # Method should execute without error
        # The actual behavior is determined by the model implementation
