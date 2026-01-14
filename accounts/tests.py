"""
Tests for user authentication and password reset functionality.
"""
import pytest
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


@pytest.mark.django_db
class TestPasswordResetFlow:
    """Tests for password reset functionality."""

    def test_password_reset_request_with_valid_email(self, client):
        """Test that password reset request works with valid email."""
        # Create a test user
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='oldpassword123'
        )

        # Request password reset
        response = client.post(
            reverse('accounts:password_reset'),
            {'email': 'test@example.com'}
        )

        # Should redirect to password reset done page
        assert response.status_code == 302
        assert 'password-reset/done' in response.url

    def test_password_reset_email_sent(self, client):
        """Test that password reset email is actually sent."""
        # Create a test user
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='oldpassword123'
        )

        # Clear any existing emails
        mail.outbox = []

        # Request password reset
        client.post(
            reverse('accounts:password_reset'),
            {'email': 'test@example.com'}
        )

        # Verify email was sent
        assert len(mail.outbox) == 1
        assert 'test@example.com' in mail.outbox[0].to
        assert 'password reset' in mail.outbox[0].subject.lower()

    def test_password_reset_confirmation_with_valid_token(self, client):
        """Test password reset confirmation with valid token."""
        # Create a test user
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='oldpassword123'
        )

        # Generate valid token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Submit new password with valid token
        response = client.post(
            reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token}),
            {
                'new_password1': 'newpassword123',
                'new_password2': 'newpassword123'
            }
        )

        # Should redirect to password reset complete page
        assert response.status_code == 302

        # Verify user can login with new password
        user.refresh_from_db()
        assert user.check_password('newpassword123')

    def test_password_reset_with_invalid_token(self, client):
        """Test that password reset fails with invalid/expired token."""
        # Create a test user
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='oldpassword123'
        )

        # Use an invalid token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        invalid_token = 'invalid-token-12345'

        # Try to submit new password with invalid token
        response = client.post(
            reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': invalid_token}),
            {
                'new_password1': 'newpassword123',
                'new_password2': 'newpassword123'
            }
        )

        # Should show error - password should not be changed
        user.refresh_from_db()
        assert user.check_password('oldpassword123')
        assert not user.check_password('newpassword123')

    def test_new_password_validation_minimum_8_characters(self, client):
        """Test that new password must be minimum 8 characters."""
        # Create a test user
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='oldpassword123'
        )

        # Generate valid token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Try to set password that's too short (less than 8 characters)
        response = client.post(
            reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token}),
            {
                'new_password1': 'short',
                'new_password2': 'short'
            }
        )

        # Should show validation error
        assert response.status_code == 200  # Stays on same page

        # Password should not be changed
        user.refresh_from_db()
        assert user.check_password('oldpassword123')
        assert not user.check_password('short')

    def test_password_reset_request_with_nonexistent_email(self, client):
        """Test password reset request with email that doesn't exist."""
        # Request password reset for non-existent email
        response = client.post(
            reverse('accounts:password_reset'),
            {'email': 'nonexistent@example.com'}
        )

        # Should still redirect (security: don't reveal which emails exist)
        assert response.status_code == 302

        # But no email should be sent
        assert len(mail.outbox) == 0

    def test_password_reset_passwords_must_match(self, client):
        """Test that password confirmation must match new password."""
        # Create a test user
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='oldpassword123'
        )

        # Generate valid token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Try to set mismatched passwords
        response = client.post(
            reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token}),
            {
                'new_password1': 'newpassword123',
                'new_password2': 'differentpassword123'
            }
        )

        # Should show validation error
        assert response.status_code == 200  # Stays on same page

        # Password should not be changed
        user.refresh_from_db()
        assert user.check_password('oldpassword123')
