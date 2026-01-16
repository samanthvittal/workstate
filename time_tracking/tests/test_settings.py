"""
Tests for user time tracking settings and preferences.

Tests cover settings form validation, preferences save functionality,
and default value initialization for new users.
"""
import pytest
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal

from time_tracking.models import UserTimePreferences
from time_tracking.forms import UserTimePreferencesForm


@pytest.mark.django_db
class TestUserTimePreferencesForm(TestCase):
    """Test UserTimePreferencesForm validation and behavior."""

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_form_saves_preferences_with_valid_data(self):
        """Test that form saves preferences correctly with valid data."""
        form_data = {
            'rounding_interval': 15,
            'rounding_method': 'nearest',
            'idle_threshold_minutes': 10,
            'pomodoro_work_minutes': 30,
            'pomodoro_break_minutes': 10,
            'default_billable_rate': Decimal('75.00'),
            'default_currency': 'EUR',
        }

        form = UserTimePreferencesForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

        prefs = form.save()

        self.assertEqual(prefs.user, self.user)
        self.assertEqual(prefs.rounding_interval, 15)
        self.assertEqual(prefs.rounding_method, 'nearest')
        self.assertEqual(prefs.idle_threshold_minutes, 10)
        self.assertEqual(prefs.pomodoro_work_minutes, 30)
        self.assertEqual(prefs.pomodoro_break_minutes, 10)
        self.assertEqual(prefs.default_billable_rate, Decimal('75.00'))
        self.assertEqual(prefs.default_currency, 'EUR')

    def test_form_validates_idle_threshold_minimum(self):
        """Test that idle threshold must be at least 1 minute."""
        form_data = {
            'rounding_interval': 0,
            'rounding_method': 'nearest',
            'idle_threshold_minutes': 0,
            'pomodoro_work_minutes': 25,
            'pomodoro_break_minutes': 5,
        }

        form = UserTimePreferencesForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('idle_threshold_minutes', form.errors)

    def test_form_validates_pomodoro_work_minimum(self):
        """Test that Pomodoro work interval must be at least 5 minutes."""
        form_data = {
            'rounding_interval': 0,
            'rounding_method': 'nearest',
            'idle_threshold_minutes': 5,
            'pomodoro_work_minutes': 3,
            'pomodoro_break_minutes': 5,
        }

        form = UserTimePreferencesForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('pomodoro_work_minutes', form.errors)

    def test_form_validates_pomodoro_break_minimum(self):
        """Test that Pomodoro break interval must be at least 1 minute."""
        form_data = {
            'rounding_interval': 0,
            'rounding_method': 'nearest',
            'idle_threshold_minutes': 5,
            'pomodoro_work_minutes': 25,
            'pomodoro_break_minutes': 0,
        }

        form = UserTimePreferencesForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('pomodoro_break_minutes', form.errors)

    def test_form_validates_billable_rate_non_negative(self):
        """Test that billable rate must be non-negative."""
        form_data = {
            'rounding_interval': 0,
            'rounding_method': 'nearest',
            'idle_threshold_minutes': 5,
            'pomodoro_work_minutes': 25,
            'pomodoro_break_minutes': 5,
            'default_billable_rate': Decimal('-10.00'),
            'default_currency': 'USD',
        }

        form = UserTimePreferencesForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('default_billable_rate', form.errors)


@pytest.mark.django_db
class TestTimeTrackingSettingsView(TestCase):
    """Test time tracking settings view and save functionality."""

    def setUp(self):
        """Create test user and client."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        self.settings_url = reverse('time_tracking:settings')

    def test_settings_page_displays_for_authenticated_user(self):
        """Test that settings page displays correctly for authenticated user."""
        response = self.client.get(self.settings_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'time_tracking/settings.html')
        self.assertIn('form', response.context)

    def test_settings_create_preferences_for_new_user(self):
        """Test that preferences are created with defaults for new user."""
        # Ensure no preferences exist
        UserTimePreferences.objects.filter(user=self.user).delete()

        form_data = {
            'rounding_interval': 5,
            'rounding_method': 'up',
            'idle_threshold_minutes': 7,
            'pomodoro_work_minutes': 25,
            'pomodoro_break_minutes': 5,
            'default_billable_rate': '',
            'default_currency': 'USD',
        }

        response = self.client.post(self.settings_url, data=form_data)

        # Should redirect after successful save
        self.assertEqual(response.status_code, 302)

        # Verify preferences were created
        prefs = UserTimePreferences.objects.get(user=self.user)
        self.assertEqual(prefs.rounding_interval, 5)
        self.assertEqual(prefs.rounding_method, 'up')
        self.assertEqual(prefs.idle_threshold_minutes, 7)

    def test_settings_update_existing_preferences(self):
        """Test that existing preferences are updated correctly."""
        # Create initial preferences
        prefs = UserTimePreferences.objects.create(
            user=self.user,
            rounding_interval=0,
            rounding_method='nearest',
            idle_threshold_minutes=5,
            pomodoro_work_minutes=25,
            pomodoro_break_minutes=5,
            default_currency='USD'
        )

        # Update preferences
        form_data = {
            'rounding_interval': 15,
            'rounding_method': 'down',
            'idle_threshold_minutes': 10,
            'pomodoro_work_minutes': 30,
            'pomodoro_break_minutes': 10,
            'default_billable_rate': '100.00',
            'default_currency': 'GBP',
        }

        response = self.client.post(self.settings_url, data=form_data)

        # Should redirect after successful save
        self.assertEqual(response.status_code, 302)

        # Verify preferences were updated
        prefs.refresh_from_db()
        self.assertEqual(prefs.rounding_interval, 15)
        self.assertEqual(prefs.rounding_method, 'down')
        self.assertEqual(prefs.idle_threshold_minutes, 10)
        self.assertEqual(prefs.pomodoro_work_minutes, 30)
        self.assertEqual(prefs.pomodoro_break_minutes, 10)
        self.assertEqual(prefs.default_billable_rate, Decimal('100.00'))
        self.assertEqual(prefs.default_currency, 'GBP')
