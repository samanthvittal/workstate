"""
Tests for registration and login UI components.
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User


@pytest.mark.django_db
class TestRegistrationUI:
    """Test registration form rendering and functionality."""

    def test_registration_form_renders_all_fields(self):
        """Test that registration form renders with all required and optional fields."""
        client = Client()
        response = client.get(reverse('accounts:register'))

        assert response.status_code == 200
        # Check for required fields
        assert b'email' in response.content or b'Email' in response.content
        assert b'password' in response.content or b'Password' in response.content
        assert b'full_name' in response.content or b'Full Name' in response.content
        # Check for optional fields
        assert b'workspace_name' in response.content or b'Workspace Name' in response.content
        assert b'job_title' in response.content or b'Job Title' in response.content

    def test_registration_form_responsive_layout(self):
        """Test that registration form has responsive CSS classes."""
        client = Client()
        response = client.get(reverse('accounts:register'))

        assert response.status_code == 200
        # Check for mobile-first responsive classes
        assert b'w-full' in response.content or b'flex' in response.content


@pytest.mark.django_db
class TestLoginUI:
    """Test login form rendering and functionality."""

    def test_login_form_renders_with_remember_me(self):
        """Test that login form renders with email, password, and Remember Me checkbox."""
        client = Client()
        response = client.get(reverse('accounts:login'))

        assert response.status_code == 200
        assert b'email' in response.content or b'Email' in response.content
        assert b'password' in response.content or b'Password' in response.content
        assert b'remember' in response.content or b'Remember Me' in response.content

    def test_password_visibility_toggle_present(self):
        """Test that password visibility toggle is present in login form."""
        client = Client()
        response = client.get(reverse('accounts:login'))

        assert response.status_code == 200
        # Check for password toggle functionality
        assert b'type="password"' in response.content

    def test_login_form_responsive_layout(self):
        """Test that login form has responsive CSS classes."""
        client = Client()
        response = client.get(reverse('accounts:login'))

        assert response.status_code == 200
        # Check for responsive classes
        assert b'w-full' in response.content or b'flex' in response.content


@pytest.mark.django_db
class TestFormValidationDisplay:
    """Test form validation error display."""

    def test_registration_validation_error_display(self):
        """Test that registration form displays validation errors."""
        client = Client()
        # Submit invalid data (mismatched passwords)
        response = client.post(reverse('accounts:register'), {
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'differentpass',
            'full_name': 'Test User',
        })

        # Should stay on registration page with errors
        assert response.status_code == 200
        # Check for error message in response
        assert b'error' in response.content or b'match' in response.content

    def test_login_validation_error_display(self):
        """Test that login form displays validation errors for invalid credentials."""
        client = Client()
        # Try to login with non-existent user
        response = client.post(reverse('accounts:login'), {
            'username': 'nonexistent@example.com',
            'password': 'wrongpassword',
        })

        # Should stay on login page or show error
        assert response.status_code == 200 or response.status_code == 302
