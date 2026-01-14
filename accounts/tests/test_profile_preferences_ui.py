"""
Tests for profile and preferences UI pages.
"""
import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from accounts.models import UserProfile, UserPreference


@pytest.mark.django_db
class TestProfilePageUI:
    """Tests for profile page rendering and functionality."""

    def test_profile_page_renders_user_data(self):
        """Test that profile page renders current user data correctly."""
        # Create user with profile
        user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        profile = UserProfile.objects.create(
            user=user,
            full_name='Test User',
            job_title='Software Developer',
            company='Test Company',
            phone_number='123-456-7890',
            timezone='America/New_York'
        )

        # Login and access profile page
        client = Client()
        client.login(username='testuser@example.com', password='testpass123')
        response = client.get(reverse('accounts:profile'))

        assert response.status_code == 200
        assert b'Test User' in response.content
        assert b'testuser@example.com' in response.content
        assert b'Software Developer' in response.content
        assert b'Test Company' in response.content
        assert b'123-456-7890' in response.content

    def test_avatar_upload_field_present(self):
        """Test that avatar upload field is present in profile form."""
        user = User.objects.create_user(
            username='testuser2@example.com',
            email='testuser2@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=user)

        client = Client()
        client.login(username='testuser2@example.com', password='testpass123')
        response = client.get(reverse('accounts:profile'))

        assert response.status_code == 200
        assert b'type="file"' in response.content
        assert b'avatar' in response.content.lower()

    def test_email_field_readonly(self):
        """Test that email field is read-only with disabled styling."""
        user = User.objects.create_user(
            username='testuser3@example.com',
            email='testuser3@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=user)

        client = Client()
        client.login(username='testuser3@example.com', password='testpass123')
        response = client.get(reverse('accounts:profile'))

        assert response.status_code == 200
        # Check for disabled or readonly attribute on email field
        assert (b'disabled' in response.content or b'readonly' in response.content)

    def test_profile_page_responsive_layout(self):
        """Test that profile page has responsive design classes."""
        user = User.objects.create_user(
            username='testuser4@example.com',
            email='testuser4@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=user)

        client = Client()
        client.login(username='testuser4@example.com', password='testpass123')
        response = client.get(reverse('accounts:profile'))

        assert response.status_code == 200
        # Check for Tailwind responsive classes
        content = response.content.decode('utf-8')
        assert ('sm:' in content or 'md:' in content or 'lg:' in content)


@pytest.mark.django_db
class TestPreferencesPageUI:
    """Tests for preferences page rendering and functionality."""

    def test_preferences_page_renders_settings(self):
        """Test that preferences page renders current user settings."""
        user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        preference = UserPreference.objects.create(
            user=user,
            timezone='America/Los_Angeles',
            date_format='DD/MM/YYYY',
            time_format='24',
            week_start_day='Monday'
        )

        client = Client()
        client.login(username='testuser@example.com', password='testpass123')
        response = client.get(reverse('accounts:preferences'))

        assert response.status_code == 200
        assert b'America/Los_Angeles' in response.content
        assert b'DD/MM/YYYY' in response.content
        assert b'24' in response.content or b'24-hour' in response.content
        assert b'Monday' in response.content

    def test_timezone_auto_detection_indicator(self):
        """Test that timezone field has auto-detection indicator."""
        user = User.objects.create_user(
            username='testuser2@example.com',
            email='testuser2@example.com',
            password='testpass123'
        )
        UserPreference.objects.create(user=user)

        client = Client()
        client.login(username='testuser2@example.com', password='testpass123')
        response = client.get(reverse('accounts:preferences'))

        assert response.status_code == 200
        content = response.content.decode('utf-8')
        # Check for Alpine.js or detection-related code
        assert ('x-data' in content or 'alpine' in content.lower() or 'detect' in content.lower())

    def test_date_format_dropdown_with_examples(self):
        """Test that date format dropdown shows visual examples."""
        user = User.objects.create_user(
            username='testuser3@example.com',
            email='testuser3@example.com',
            password='testpass123'
        )
        UserPreference.objects.create(user=user)

        client = Client()
        client.login(username='testuser3@example.com', password='testpass123')
        response = client.get(reverse('accounts:preferences'))

        assert response.status_code == 200
        content = response.content.decode('utf-8')
        # Check for date format options
        assert 'MM/DD/YYYY' in content
        assert 'DD/MM/YYYY' in content
        assert 'YYYY-MM-DD' in content

    def test_time_format_radio_buttons(self):
        """Test that time format shows radio buttons with examples."""
        user = User.objects.create_user(
            username='testuser4@example.com',
            email='testuser4@example.com',
            password='testpass123'
        )
        UserPreference.objects.create(user=user)

        client = Client()
        client.login(username='testuser4@example.com', password='testpass123')
        response = client.get(reverse('accounts:preferences'))

        assert response.status_code == 200
        content = response.content.decode('utf-8')
        # Check for time format radio buttons
        assert 'type="radio"' in content
        assert ('12-hour' in content or '12' in content)
        assert ('24-hour' in content or '24' in content)

    def test_preferences_page_responsive_layout(self):
        """Test that preferences page has responsive design classes."""
        user = User.objects.create_user(
            username='testuser5@example.com',
            email='testuser5@example.com',
            password='testpass123'
        )
        UserPreference.objects.create(user=user)

        client = Client()
        client.login(username='testuser5@example.com', password='testpass123')
        response = client.get(reverse('accounts:preferences'))

        assert response.status_code == 200
        content = response.content.decode('utf-8')
        # Check for Tailwind responsive classes
        assert ('sm:' in content or 'md:' in content or 'lg:' in content)
