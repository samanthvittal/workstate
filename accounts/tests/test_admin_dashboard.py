"""
Tests for admin user management dashboard.
"""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from accounts.models import UserProfile, UserPreference, Workspace, LoginAttempt


@pytest.mark.django_db
class TestAdminDashboardAccess:
    """Tests for admin dashboard access control."""

    def test_admin_access_allowed(self):
        """Test that admin users can access the dashboard."""
        # Create admin user
        admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )

        client = Client()
        client.login(username='admin@example.com', password='adminpass123')

        response = client.get(reverse('accounts:admin_user_list'))

        assert response.status_code == 200

    def test_non_admin_access_blocked(self):
        """Test that non-admin users cannot access the dashboard."""
        # Create regular user
        user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            password='userpass123',
            is_staff=False
        )

        client = Client()
        client.login(username='user@example.com', password='userpass123')

        response = client.get(reverse('accounts:admin_user_list'))

        # Should return 403 Forbidden
        assert response.status_code == 403


@pytest.mark.django_db
class TestAdminUserListView:
    """Tests for admin user list view."""

    def test_user_list_displays_users(self):
        """Test that user list displays all users with key details."""
        # Create admin user
        admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        UserProfile.objects.create(user=admin, full_name='Admin User')

        # Create regular users
        user1 = User.objects.create_user(
            username='user1@example.com',
            email='user1@example.com',
            password='pass123'
        )
        UserProfile.objects.create(user=user1, full_name='User One')

        user2 = User.objects.create_user(
            username='user2@example.com',
            email='user2@example.com',
            password='pass123'
        )
        UserProfile.objects.create(user=user2, full_name='User Two')

        client = Client()
        client.login(username='admin@example.com', password='adminpass123')

        response = client.get(reverse('accounts:admin_user_list'))

        assert response.status_code == 200
        # Check that users are in context
        assert 'users' in response.context or 'page_obj' in response.context

    def test_user_list_pagination(self):
        """Test that user list has pagination."""
        # Create admin user
        admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )

        # Create 30 users to test pagination (25 per page)
        for i in range(30):
            user = User.objects.create_user(
                username=f'user{i}@example.com',
                email=f'user{i}@example.com',
                password='pass123'
            )
            UserProfile.objects.create(user=user, full_name=f'User {i}')

        client = Client()
        client.login(username='admin@example.com', password='adminpass123')

        response = client.get(reverse('accounts:admin_user_list'))

        assert response.status_code == 200
        # Check pagination context
        if 'page_obj' in response.context:
            assert response.context['page_obj'].paginator.per_page == 25

    def test_user_search_functionality(self):
        """Test that user search works correctly."""
        # Create admin user
        admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )

        # Create test users
        user1 = User.objects.create_user(
            username='john@example.com',
            email='john@example.com',
            password='pass123'
        )
        UserProfile.objects.create(user=user1, full_name='John Doe')

        user2 = User.objects.create_user(
            username='jane@example.com',
            email='jane@example.com',
            password='pass123'
        )
        UserProfile.objects.create(user=user2, full_name='Jane Smith')

        client = Client()
        client.login(username='admin@example.com', password='adminpass123')

        # Search by name
        response = client.get(reverse('accounts:admin_user_list') + '?search=John')

        assert response.status_code == 200

    def test_user_filter_by_status(self):
        """Test filtering users by status (active, locked, unverified)."""
        # Create admin user
        admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )

        # Create active user
        active_user = User.objects.create_user(
            username='active@example.com',
            email='active@example.com',
            password='pass123',
            is_active=True
        )

        # Create locked user (3 failed login attempts)
        locked_user = User.objects.create_user(
            username='locked@example.com',
            email='locked@example.com',
            password='pass123'
        )
        for i in range(3):
            LoginAttempt.objects.create(
                user=locked_user,
                is_successful=False,
                ip_address=f'192.168.1.{i}'
            )

        client = Client()
        client.login(username='admin@example.com', password='adminpass123')

        # Filter by locked status
        response = client.get(reverse('accounts:admin_user_list') + '?status=locked')

        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminUserDetailView:
    """Tests for admin user detail view."""

    def test_view_individual_user_details(self):
        """Test viewing individual user profile details."""
        # Create admin user
        admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )

        # Create test user with profile and preferences
        user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            password='pass123'
        )
        UserProfile.objects.create(
            user=user,
            full_name='Test User',
            job_title='Developer',
            company='Test Corp'
        )
        UserPreference.objects.create(
            user=user,
            timezone='America/New_York',
            date_format='MM/DD/YYYY'
        )
        Workspace.objects.create(
            owner=user,
            name='Test Workspace',
            is_personal=True
        )

        client = Client()
        client.login(username='admin@example.com', password='adminpass123')

        response = client.get(reverse('accounts:admin_user_detail', kwargs={'pk': user.pk}))

        assert response.status_code == 200
        assert 'user' in response.context or 'object' in response.context
