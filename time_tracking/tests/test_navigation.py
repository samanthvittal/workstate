"""
Tests for time tracking navigation and URL routing.

Focus on critical URL resolution and navigation functionality.
"""
from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from tasks.models import TaskList, Task
from time_tracking.views.time_entry_list_views import TimeEntryListHTMLView
from time_tracking.views.time_entry_form_views import TimeEntryCreateFormView
from time_tracking.views.analytics_views import AnalyticsDashboardView
from time_tracking.views.settings_views import TimeTrackingSettingsView

User = get_user_model()


class NavigationURLResolutionTestCase(TestCase):
    """Test that critical time tracking URLs resolve correctly."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_time_entry_list_url_resolves(self):
        """Time entry list URL resolves to correct view."""
        url = reverse('time_tracking:time-entry-list-html')
        self.assertEqual(url, '/entries/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, TimeEntryListHTMLView)

    def test_time_entry_create_url_resolves(self):
        """Time entry create URL resolves to correct view."""
        url = reverse('time_tracking:time-entry-create-form')
        self.assertEqual(url, '/entries/new/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, TimeEntryCreateFormView)

    def test_analytics_dashboard_url_resolves(self):
        """Analytics dashboard URL resolves to correct view."""
        url = reverse('time_tracking:analytics-dashboard')
        self.assertEqual(url, '/analytics/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, AnalyticsDashboardView)

    def test_settings_url_resolves(self):
        """Settings URL resolves to correct view."""
        url = reverse('time_tracking:settings')
        self.assertEqual(url, '/settings/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, TimeTrackingSettingsView)


class NavigationAccessibilityTestCase(TestCase):
    """Test that authenticated users can access time tracking pages."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_time_entry_list_accessible_when_authenticated(self):
        """Time entry list page is accessible to authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('time_tracking:time-entry-list-html'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Time Entries')

    def test_analytics_dashboard_accessible_when_authenticated(self):
        """Analytics dashboard is accessible to authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('time_tracking:analytics-dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analytics Dashboard')

    def test_settings_accessible_when_authenticated(self):
        """Settings page is accessible to authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('time_tracking:settings'))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_users_redirected_to_login(self):
        """Unauthenticated users are redirected to login page."""
        response = self.client.get(reverse('time_tracking:time-entry-list-html'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class TimerAPIURLResolutionTestCase(TestCase):
    """Test that timer API URLs resolve correctly."""

    def test_timer_start_url_resolves(self):
        """Timer start API URL resolves correctly."""
        url = reverse('time_tracking:timer-start')
        self.assertEqual(url, '/api/timers/start/')

    def test_timer_stop_url_resolves(self):
        """Timer stop API URL resolves correctly."""
        url = reverse('time_tracking:timer-stop')
        self.assertEqual(url, '/api/timers/stop/')

    def test_timer_active_url_resolves(self):
        """Timer get active API URL resolves correctly."""
        url = reverse('time_tracking:timer-get-active')
        self.assertEqual(url, '/api/timers/active/')

    def test_timer_discard_url_resolves(self):
        """Timer discard API URL resolves correctly."""
        url = reverse('time_tracking:timer-discard')
        self.assertEqual(url, '/api/timers/discard/')
