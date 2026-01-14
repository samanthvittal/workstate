"""
Tests for user profile management functionality.
"""
import pytest
import os
from io import BytesIO
from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from accounts.models import UserProfile


@pytest.mark.django_db
class TestProfileManagement:
    """Tests for profile management endpoints."""

    def test_profile_view_loads_current_user_data(self, client):
        """Test that profile view loads and displays current user data."""
        # Create a test user with profile
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
        profile = UserProfile.objects.create(
            user=user,
            full_name='Test User',
            job_title='Developer',
            company='Test Corp',
            phone_number='+1234567890',
            timezone='America/New_York'
        )

        # Login the user
        client.login(username='test@example.com', password='testpass123')

        # Access profile page
        response = client.get(reverse('accounts:profile'))

        # Should return 200 and display user data
        assert response.status_code == 200
        assert 'Test User' in str(response.content)
        assert 'test@example.com' in str(response.content)

    def test_profile_update_with_valid_data(self, client):
        """Test profile update with valid data saves correctly."""
        # Create a test user
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=user, full_name='Old Name')

        # Login
        client.login(username='test@example.com', password='testpass123')

        # Update profile
        response = client.post(
            reverse('accounts:profile_edit'),
            {
                'full_name': 'New Name',
                'job_title': 'Senior Developer',
                'company': 'New Company',
                'phone_number': '+9876543210',
                'timezone': 'Europe/London'
            }
        )

        # Should redirect to profile page
        assert response.status_code == 302

        # Verify data was updated
        user.refresh_from_db()
        profile = user.profile
        assert profile.full_name == 'New Name'
        assert profile.job_title == 'Senior Developer'
        assert profile.company == 'New Company'
        assert profile.phone_number == '+9876543210'
        assert profile.timezone == 'Europe/London'

    def test_avatar_upload_and_validation(self, client):
        """Test avatar upload with valid image file."""
        # Create a test user
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=user)

        # Login
        client.login(username='test@example.com', password='testpass123')

        # Create a test image
        image = Image.new('RGB', (100, 100), color='red')
        image_file = BytesIO()
        image.save(image_file, 'PNG')
        image_file.seek(0)

        uploaded_file = SimpleUploadedFile(
            'test_avatar.png',
            image_file.read(),
            content_type='image/png'
        )

        # Upload avatar
        response = client.post(
            reverse('accounts:profile_edit'),
            {
                'full_name': 'Test User',
                'timezone': 'UTC',
                'avatar': uploaded_file
            }
        )

        # Should succeed
        assert response.status_code == 302

        # Verify avatar was saved
        user.refresh_from_db()
        assert user.profile.avatar
        assert 'avatars/' in user.profile.avatar.name

        # Clean up uploaded file
        if user.profile.avatar:
            user.profile.avatar.delete()

    def test_avatar_validation_invalid_file_type(self, client):
        """Test that invalid file types are rejected for avatar upload."""
        # Create a test user
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=user)

        # Login
        client.login(username='test@example.com', password='testpass123')

        # Create a non-image file
        invalid_file = SimpleUploadedFile(
            'test.txt',
            b'This is not an image',
            content_type='text/plain'
        )

        # Try to upload as avatar
        response = client.post(
            reverse('accounts:profile_edit'),
            {
                'full_name': 'Test User',
                'timezone': 'UTC',
                'avatar': invalid_file
            }
        )

        # Should show validation error (stays on page)
        assert response.status_code == 200
        # Avatar should not be saved
        user.refresh_from_db()
        assert not user.profile.avatar

    def test_email_field_is_read_only(self, client):
        """Test that email field cannot be changed via profile update."""
        # Create a test user
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=user)

        # Login
        client.login(username='test@example.com', password='testpass123')

        # Try to update profile with email field (should be ignored)
        response = client.post(
            reverse('accounts:profile_edit'),
            {
                'email': 'newemail@example.com',  # This should be ignored
                'full_name': 'Test User',
                'timezone': 'UTC'
            }
        )

        # Email should remain unchanged
        user.refresh_from_db()
        assert user.email == 'test@example.com'
        assert user.email != 'newemail@example.com'

    def test_validation_errors_display_inline(self, client):
        """Test that validation errors are displayed properly."""
        # Create a test user
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=user)

        # Login
        client.login(username='test@example.com', password='testpass123')

        # Submit invalid timezone
        response = client.post(
            reverse('accounts:profile_edit'),
            {
                'full_name': 'Test User',
                'timezone': 'Invalid/Timezone'
            }
        )

        # Should stay on page with error
        assert response.status_code == 200
        # Check for form errors in response
        assert b'form' in response.content or b'error' in response.content

    def test_profile_requires_authentication(self, client):
        """Test that profile pages require user to be logged in."""
        # Try to access profile without logging in
        response = client.get(reverse('accounts:profile'))

        # Should redirect to login
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
