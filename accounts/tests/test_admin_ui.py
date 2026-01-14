"""
Tests for admin dashboard UI components and interactivity.
"""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from accounts.models import UserProfile, UserPreference, Workspace, LoginAttempt


@pytest.mark.django_db
class TestAdminDashboardUIAccess:
    """Tests for admin dashboard UI access control."""

    def test_admin_dashboard_access_control(self):
        """Test that admin dashboard is accessible only to admins."""
        # Create admin user
        admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )

        # Create regular user
        regular_user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            password='userpass123',
            is_staff=False
        )

        client = Client()

        # Test admin can access
        client.login(username='admin@example.com', password='adminpass123')
        response = client.get(reverse('accounts:admin_user_list'))
        assert response.status_code == 200

        # Test non-admin cannot access
        client.logout()
        client.login(username='user@example.com', password='userpass123')
        response = client.get(reverse('accounts:admin_user_list'))
        assert response.status_code == 403


@pytest.mark.django_db
class TestAdminUserListTableUI:
    """Tests for admin user list table rendering."""

    def test_user_list_table_renders(self):
        """Test that user list table renders with correct columns."""
        # Create admin user
        admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        UserProfile.objects.create(user=admin, full_name='Admin User')

        # Create test users
        user1 = User.objects.create_user(
            username='user1@example.com',
            email='user1@example.com',
            password='pass123'
        )
        UserProfile.objects.create(user=user1, full_name='Test User One')

        client = Client()
        client.login(username='admin@example.com', password='adminpass123')
        response = client.get(reverse('accounts:admin_user_list'))

        assert response.status_code == 200
        content = response.content.decode()

        # Check table headers are present
        assert 'Name' in content or 'name' in content.lower()
        assert 'Email' in content or 'email' in content.lower()
        assert 'Status' in content or 'status' in content.lower()
        assert 'Actions' in content or 'actions' in content.lower()


@pytest.mark.django_db
class TestAdminSearchFunctionalityUI:
    """Tests for admin search functionality UI."""

    def test_search_functionality_ui(self):
        """Test that search input field renders and works."""
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

        # Test search form renders
        response = client.get(reverse('accounts:admin_user_list'))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'search' in content.lower()

        # Test search with query parameter
        response = client.get(reverse('accounts:admin_user_list') + '?search=John')
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminFilterDropdownUI:
    """Tests for admin filter dropdown UI."""

    def test_filter_dropdown_ui(self):
        """Test that filter dropdown renders with status options."""
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
        content = response.content.decode()

        # Check filter options are present
        assert 'filter' in content.lower() or 'status' in content.lower()


@pytest.mark.django_db
class TestAdminActionButtonsUI:
    """Tests for admin action buttons functionality."""

    def test_action_button_functionality(self):
        """Test that action buttons are rendered and functional."""
        # Create admin user
        admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )

        # Create test user
        user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            password='pass123'
        )
        UserProfile.objects.create(user=user, full_name='Test User')

        client = Client()
        client.login(username='admin@example.com', password='adminpass123')

        # Test user detail page has action buttons
        response = client.get(reverse('accounts:admin_user_detail', kwargs={'pk': user.pk}))
        assert response.status_code == 200
        content = response.content.decode()

        # Check for action buttons or links
        assert 'unlock' in content.lower() or 'reset' in content.lower() or 'delete' in content.lower()
