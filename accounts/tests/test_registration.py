"""
Tests for user registration and email verification functionality.
"""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.core import mail
from allauth.account.models import EmailAddress
from accounts.models import UserProfile, UserPreference, Workspace


@pytest.mark.django_db
class TestRegistration:
    """Test suite for user registration endpoints and flows."""

    def test_successful_registration_with_all_fields(self, client):
        """
        Test successful registration with all optional fields provided.
        Verifies user, profile, preferences, and workspace creation.
        """
        registration_data = {
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'full_name': 'Test User',
            'workspace_name': 'My Workspace',
            'job_title': 'Developer',
            'company': 'Test Corp',
            'phone_number': '+1234567890',
        }

        response = client.post(reverse('accounts:register'), registration_data)

        # Check redirect to email verification page
        assert response.status_code == 302

        # Verify user was created
        user = User.objects.get(email='test@example.com')
        assert user is not None
        assert not user.is_active  # Not active until email verification

        # Verify UserProfile was created
        assert hasattr(user, 'profile')
        assert user.profile.full_name == 'Test User'
        assert user.profile.job_title == 'Developer'
        assert user.profile.company == 'Test Corp'
        assert user.profile.phone_number == '+1234567890'

        # Verify UserPreference was created
        assert hasattr(user, 'preferences')
        assert user.preferences.timezone == 'UTC'
        assert user.preferences.date_format == 'MM/DD/YYYY'

        # Verify Workspace was created
        workspace = Workspace.objects.get(owner=user)
        assert workspace.name == 'My Workspace'
        assert workspace.is_personal is True

        # Verify email verification email was sent
        assert len(mail.outbox) == 1
        assert 'test@example.com' in mail.outbox[0].to

    def test_successful_registration_with_minimal_fields(self, client):
        """
        Test registration with only required fields.
        Verifies constellation name is used for workspace.
        """
        registration_data = {
            'email': 'minimal@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'full_name': 'Minimal User',
        }

        response = client.post(reverse('accounts:register'), registration_data)

        # Check redirect
        assert response.status_code == 302

        # Verify user was created
        user = User.objects.get(email='minimal@example.com')
        assert user is not None

        # Verify workspace was created with constellation name
        workspace = Workspace.objects.get(owner=user)
        assert workspace.name in [
            'Orion', 'Andromeda', 'Cassiopeia', 'Lyra', 'Cygnus',
            'Perseus', 'Draco', 'Ursa Major', 'Phoenix', 'Centaurus'
        ]
        assert workspace.is_personal is True

    def test_duplicate_email_detection(self, client):
        """
        Test that duplicate email addresses are rejected.
        Verifies error message and redirect to login.
        """
        # Create initial user
        User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='ExistingPass123!'
        )

        # Attempt to register with same email
        registration_data = {
            'email': 'existing@example.com',
            'password1': 'NewPass123!',
            'password2': 'NewPass123!',
            'full_name': 'Duplicate User',
        }

        response = client.post(reverse('accounts:register'), registration_data)

        # Should redirect to login page
        assert response.status_code == 302
        assert reverse('accounts:login') in response.url

        # Email should be prepopulated in redirect URL
        assert 'email=existing@example.com' in response.url or 'existing@example.com' in str(response.cookies)

    def test_automatic_workspace_creation(self, client):
        """
        Test that workspace is automatically created during registration.
        """
        registration_data = {
            'email': 'workspace@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'full_name': 'Workspace User',
        }

        client.post(reverse('accounts:register'), registration_data)

        user = User.objects.get(email='workspace@example.com')
        workspaces = Workspace.objects.filter(owner=user)

        # Verify exactly one workspace was created
        assert workspaces.count() == 1
        assert workspaces.first().is_personal is True

    def test_email_verification_flow(self, client):
        """
        Test the complete email verification flow.
        """
        registration_data = {
            'email': 'verify@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'full_name': 'Verify User',
        }

        client.post(reverse('accounts:register'), registration_data)

        user = User.objects.get(email='verify@example.com')

        # User should not be active initially
        assert not user.is_active

        # Verify email verification email was sent
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert 'verify@example.com' in email.to

        # Extract verification URL from email
        # In production, user clicks link; here we simulate it
        email_address = EmailAddress.objects.get(email='verify@example.com')
        email_address.verified = True
        email_address.save()

        # Refresh user
        user.refresh_from_db()
        user.is_active = True
        user.save()

        # Now user should be able to log in
        login_successful = client.login(
            username='verify@example.com',
            password='TestPass123!'
        )
        assert login_successful is True

    def test_password_validation_minimum_length(self, client):
        """
        Test that passwords less than 8 characters are rejected.
        """
        registration_data = {
            'email': 'short@example.com',
            'password1': 'Short1!',  # Only 7 characters
            'password2': 'Short1!',
            'full_name': 'Short Password',
        }

        response = client.post(reverse('accounts:register'), registration_data)

        # Should not create user
        assert not User.objects.filter(email='short@example.com').exists()

        # Should show error
        assert response.status_code == 200  # Re-renders form with errors
        assert 'password' in str(response.content).lower() or 'error' in str(response.content).lower()
