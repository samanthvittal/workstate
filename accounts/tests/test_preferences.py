"""
Tests for user preferences functionality.
"""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from accounts.models import UserPreference


@pytest.mark.django_db
class TestPreferencesView:
    """Tests for preferences view and update functionality."""

    def test_preferences_view_loads_current_settings(self):
        """Test that preferences view displays user's current preference settings."""
        # Create user with preferences
        user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        preferences = UserPreference.objects.create(
            user=user,
            timezone='America/New_York',
            date_format='DD/MM/YYYY',
            time_format='24',
            week_start_day='Monday'
        )

        # Log in and access preferences page
        client = Client()
        client.login(username='testuser@example.com', password='testpass123')
        response = client.get(reverse('preferences'))

        assert response.status_code == 200
        assert 'America/New_York' in str(response.content)
        assert 'DD/MM/YYYY' in str(response.content)

    def test_preferences_update_with_valid_choices(self):
        """Test updating preferences with valid data saves correctly."""
        user = User.objects.create_user(
            username='testuser2@example.com',
            email='testuser2@example.com',
            password='testpass123'
        )
        # Create initial preferences
        UserPreference.objects.create(user=user)

        client = Client()
        client.login(username='testuser2@example.com', password='testpass123')

        # Update preferences
        response = client.post(reverse('preferences'), {
            'timezone': 'Europe/London',
            'date_format': 'YYYY-MM-DD',
            'time_format': '24',
            'week_start_day': 'Monday'
        })

        # Check redirect or success
        assert response.status_code in [200, 302]

        # Verify preferences were updated
        preferences = UserPreference.objects.get(user=user)
        assert preferences.timezone == 'Europe/London'
        assert preferences.date_format == 'YYYY-MM-DD'
        assert preferences.time_format == '24'
        assert preferences.week_start_day == 'Monday'

    def test_timezone_auto_detection_from_browser(self):
        """Test that timezone can be auto-detected from browser (via Alpine.js)."""
        user = User.objects.create_user(
            username='testuser3@example.com',
            email='testuser3@example.com',
            password='testpass123'
        )
        UserPreference.objects.create(user=user)

        client = Client()
        client.login(username='testuser3@example.com', password='testpass123')

        # Simulate browser-detected timezone being sent
        response = client.post(reverse('preferences'), {
            'timezone': 'America/Los_Angeles',  # Browser-detected timezone
            'date_format': 'MM/DD/YYYY',
            'time_format': '12',
            'week_start_day': 'Sunday'
        })

        assert response.status_code in [200, 302]

        # Verify timezone was set
        preferences = UserPreference.objects.get(user=user)
        assert preferences.timezone == 'America/Los_Angeles'


@pytest.mark.django_db
class TestDateTimeFilters:
    """Tests for custom date/time template filters."""

    def test_date_format_application_across_app(self):
        """Test that date format preference is applied correctly in templates."""
        from accounts.templatetags.preference_filters import user_date
        from datetime import date

        user = User.objects.create_user(
            username='testuser4@example.com',
            email='testuser4@example.com',
            password='testpass123'
        )

        # Test MM/DD/YYYY format
        prefs_mm = UserPreference.objects.create(
            user=user,
            date_format='MM/DD/YYYY'
        )
        test_date = date(2024, 3, 15)
        formatted = user_date(test_date, user)
        assert formatted == '03/15/2024'

        # Test DD/MM/YYYY format
        prefs_mm.date_format = 'DD/MM/YYYY'
        prefs_mm.save()
        formatted = user_date(test_date, user)
        assert formatted == '15/03/2024'

        # Test YYYY-MM-DD format
        prefs_mm.date_format = 'YYYY-MM-DD'
        prefs_mm.save()
        formatted = user_date(test_date, user)
        assert formatted == '2024-03-15'

    def test_time_format_application_12_hour(self):
        """Test that 12-hour time format is applied correctly."""
        from accounts.templatetags.preference_filters import user_time
        from datetime import time as dt_time

        user = User.objects.create_user(
            username='testuser5@example.com',
            email='testuser5@example.com',
            password='testpass123'
        )

        UserPreference.objects.create(
            user=user,
            time_format='12'
        )

        # Test afternoon time
        test_time = dt_time(14, 30, 0)
        formatted = user_time(test_time, user)
        assert '2:30' in formatted or '02:30' in formatted
        assert 'PM' in formatted

    def test_time_format_application_24_hour(self):
        """Test that 24-hour time format is applied correctly."""
        from accounts.templatetags.preference_filters import user_time
        from datetime import time as dt_time

        user = User.objects.create_user(
            username='testuser6@example.com',
            email='testuser6@example.com',
            password='testpass123'
        )

        UserPreference.objects.create(
            user=user,
            time_format='24'
        )

        # Test afternoon time
        test_time = dt_time(14, 30, 0)
        formatted = user_time(test_time, user)
        assert '14:30' in formatted
        assert 'PM' not in formatted


@pytest.mark.django_db
class TestPreferencesForm:
    """Tests for PreferencesUpdateForm validation."""

    def test_form_accepts_valid_timezone(self):
        """Test that form accepts valid timezone choices."""
        from accounts.forms import PreferencesUpdateForm

        form = PreferencesUpdateForm(data={
            'timezone': 'America/Chicago',
            'date_format': 'MM/DD/YYYY',
            'time_format': '12',
            'week_start_day': 'Sunday'
        })

        assert form.is_valid()

    def test_form_rejects_invalid_date_format(self):
        """Test that form rejects invalid date format choice."""
        from accounts.forms import PreferencesUpdateForm

        form = PreferencesUpdateForm(data={
            'timezone': 'UTC',
            'date_format': 'INVALID',
            'time_format': '12',
            'week_start_day': 'Sunday'
        })

        assert not form.is_valid()
        assert 'date_format' in form.errors
