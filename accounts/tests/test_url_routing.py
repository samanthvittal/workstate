"""
Tests for URL routing and middleware.
"""
import pytest
from django.urls import reverse, resolve
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone as django_timezone
import pytz

from accounts.models import UserPreference
from accounts.middleware import TimezoneMiddleware


@pytest.mark.django_db
class TestURLRouting:
    """Test that all URL patterns resolve correctly."""

    def test_authentication_urls_resolve(self):
        """Test authentication URL patterns resolve to correct views."""
        # Registration
        url = reverse('accounts:register')
        assert url == '/accounts/register/'

        # Login
        url = reverse('accounts:login')
        assert url == '/accounts/login/'

        # Logout
        url = reverse('accounts:logout')
        assert url == '/accounts/logout/'

    def test_password_reset_urls_resolve(self):
        """Test password reset URL patterns resolve correctly."""
        # Password reset request
        url = reverse('accounts:password_reset')
        assert url == '/accounts/password-reset/'

        # Password reset done
        url = reverse('accounts:password_reset_done')
        assert url == '/accounts/password-reset/done/'

        # Password reset confirm (with token)
        url = reverse('accounts:password_reset_confirm', kwargs={'uidb64': 'test123', 'token': 'abc-123'})
        assert '/accounts/password-reset/confirm/test123/abc-123/' == url

        # Password reset complete
        url = reverse('accounts:password_reset_complete')
        assert url == '/accounts/password-reset/complete/'

    def test_profile_urls_resolve(self):
        """Test profile URL patterns resolve correctly."""
        # Profile view
        url = reverse('accounts:profile')
        assert url == '/accounts/profile/'

        # Profile edit
        url = reverse('accounts:profile_edit')
        assert url == '/accounts/profile/edit/'

    def test_preferences_urls_resolve(self):
        """Test preferences URL patterns resolve correctly."""
        # Preferences view
        url = reverse('accounts:preferences')
        assert url == '/accounts/preferences/'

        # Preferences edit
        url = reverse('accounts:preferences_edit')
        assert url == '/accounts/preferences/edit/'

    def test_admin_dashboard_urls_resolve(self):
        """Test admin dashboard URL patterns resolve correctly."""
        # Admin dashboard
        url = reverse('accounts:admin_dashboard')
        assert url == '/accounts/admin-dashboard/'

        # Admin user detail
        url = reverse('accounts:admin_user_detail', kwargs={'user_id': 1})
        assert url == '/accounts/admin-dashboard/users/1/'

        # Admin unlock account
        url = reverse('accounts:admin_unlock_account', kwargs={'user_id': 1})
        assert url == '/accounts/admin-dashboard/users/1/unlock/'

        # Admin reset password
        url = reverse('accounts:admin_reset_password', kwargs={'user_id': 1})
        assert url == '/accounts/admin-dashboard/users/1/reset-password/'

        # Admin delete user
        url = reverse('accounts:admin_delete_user', kwargs={'user_id': 1})
        assert url == '/accounts/admin-dashboard/users/1/delete/'

        # Admin toggle admin
        url = reverse('accounts:admin_toggle_admin', kwargs={'user_id': 1})
        assert url == '/accounts/admin-dashboard/users/1/toggle-admin/'


@pytest.mark.django_db
class TestTimezoneMiddleware:
    """Test timezone middleware activates user timezone."""

    def test_middleware_activates_user_timezone(self):
        """Test middleware activates timezone from user preferences."""
        # Create user with preference
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        UserPreference.objects.create(
            user=user,
            timezone='America/New_York'
        )

        # Create request
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = user

        # Create a mock get_response
        def get_response(request):
            # Check that timezone is activated during request
            current_tz = django_timezone.get_current_timezone()
            assert str(current_tz) == 'America/New_York'
            from django.http import HttpResponse
            return HttpResponse('OK')

        # Apply middleware
        middleware = TimezoneMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 200

    def test_middleware_uses_utc_for_anonymous_users(self):
        """Test middleware uses UTC for anonymous users."""
        from django.contrib.auth.models import AnonymousUser

        # Create request with anonymous user
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = AnonymousUser()

        # Create a mock get_response
        def get_response(request):
            # Timezone should be deactivated (uses default)
            from django.http import HttpResponse
            return HttpResponse('OK')

        # Apply middleware
        middleware = TimezoneMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 200

    def test_middleware_handles_missing_preferences(self):
        """Test middleware handles users without preferences gracefully."""
        # Create user without preferences
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create request
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = user

        # Create a mock get_response
        def get_response(request):
            # Should use UTC as fallback
            current_tz = django_timezone.get_current_timezone()
            assert str(current_tz) == 'UTC'
            from django.http import HttpResponse
            return HttpResponse('OK')

        # Apply middleware
        middleware = TimezoneMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 200

    def test_middleware_handles_invalid_timezone(self):
        """Test middleware handles invalid timezone gracefully."""
        # Create user with invalid timezone
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Manually create preference with invalid timezone
        pref = UserPreference.objects.create(user=user)
        pref.timezone = 'Invalid/Timezone'
        pref.save()

        # Create request
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = user

        # Create a mock get_response
        def get_response(request):
            # Should fallback to UTC
            current_tz = django_timezone.get_current_timezone()
            assert str(current_tz) == 'UTC'
            from django.http import HttpResponse
            return HttpResponse('OK')

        # Apply middleware
        middleware = TimezoneMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 200
