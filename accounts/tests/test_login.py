"""
Tests for login functionality and account lockout.
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from accounts.models import LoginAttempt


@pytest.mark.django_db
class LoginTestCase(TestCase):
    """Test cases for login and account lockout functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        self.login_url = reverse('accounts:login')

    def test_successful_login_with_correct_credentials(self):
        """Test that user can login with valid credentials"""
        response = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'testpass123',
        })

        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)

        # Check that a successful login attempt was recorded
        login_attempt = LoginAttempt.objects.filter(
            user=self.user,
            is_successful=True
        ).first()
        self.assertIsNotNone(login_attempt)

    def test_failed_login_with_incorrect_password(self):
        """Test that login fails with incorrect password"""
        response = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'wrongpassword',
        })

        # Should return the login form with error
        self.assertEqual(response.status_code, 200)

        # Check that a failed login attempt was recorded
        login_attempt = LoginAttempt.objects.filter(
            user=self.user,
            is_successful=False
        ).first()
        self.assertIsNotNone(login_attempt)

    def test_account_lockout_after_three_failed_attempts(self):
        """Test that account locks after 3 consecutive failed login attempts"""
        # Attempt 1
        self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'wrongpass1',
        })

        # Attempt 2
        self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'wrongpass2',
        })

        # Attempt 3
        self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'wrongpass3',
        })

        # Account should now be locked
        self.assertTrue(LoginAttempt.is_account_locked(self.user))

        # Fourth attempt should be blocked with lockout message
        response = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'testpass123',  # Even with correct password
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'locked', status_code=200)

    def test_lockout_message_displays_unlock_time(self):
        """Test that lockout message shows when account will be unlocked"""
        # Create 3 failed attempts
        for _ in range(3):
            self.client.post(self.login_url, {
                'email': 'testuser@example.com',
                'password': 'wrongpassword',
            })

        # Try to login again
        response = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'testpass123',
        })

        # Should show lockout message with unlock time
        self.assertContains(response, '30', status_code=200)
        self.assertTrue(LoginAttempt.is_account_locked(self.user))

    def test_auto_unlock_after_30_minutes(self):
        """Test that account automatically unlocks after 30 minutes"""
        # Create 3 failed attempts with timestamps 31 minutes ago
        past_time = timezone.now() - timedelta(minutes=31)
        for i in range(3):
            attempt = LoginAttempt.objects.create(
                user=self.user,
                is_successful=False,
                ip_address='127.0.0.1'
            )
            # Manually set the timestamp to 31 minutes ago
            LoginAttempt.objects.filter(pk=attempt.pk).update(timestamp=past_time)

        # Account should not be locked anymore
        self.assertFalse(LoginAttempt.is_account_locked(self.user))

        # Should be able to login successfully
        response = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'testpass123',
        })

        self.assertEqual(response.status_code, 302)

    def test_remember_me_functionality(self):
        """Test that 'Remember Me' checkbox extends session duration"""
        # Login without 'Remember Me'
        self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'testpass123',
        })

        # Check default session expiry (2 weeks)
        session = self.client.session
        default_age = session.get_expiry_age()

        # Logout
        self.client.logout()

        # Login with 'Remember Me'
        self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'testpass123',
            'remember_me': True,
        })

        # Check extended session expiry (30 days)
        session = self.client.session
        remember_age = session.get_expiry_age()

        # Remember Me session should be longer than default
        self.assertGreater(remember_age, default_age)

    def test_successful_login_resets_failed_attempts(self):
        """Test that successful login resets failed attempt counter"""
        # Create 2 failed attempts
        for _ in range(2):
            self.client.post(self.login_url, {
                'email': 'testuser@example.com',
                'password': 'wrongpassword',
            })

        # Verify 2 failed attempts exist
        failed_count = LoginAttempt.objects.filter(
            user=self.user,
            is_successful=False
        ).count()
        self.assertEqual(failed_count, 2)

        # Successful login
        self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'testpass123',
        })

        # Account should not be locked
        self.assertFalse(LoginAttempt.is_account_locked(self.user))

        # Should have a successful login attempt
        successful_attempt = LoginAttempt.objects.filter(
            user=self.user,
            is_successful=True
        ).exists()
        self.assertTrue(successful_attempt)
