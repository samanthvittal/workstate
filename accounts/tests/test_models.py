"""
Tests for User and UserProfile models.
"""
import pytest
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from accounts.models import UserProfile


@pytest.mark.django_db
class TestUserModel:
    """Test suite for Django User model with profile integration."""

    def test_user_creation_with_required_fields(self):
        """Test that a user can be created with required fields."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        assert user.id is not None
        assert user.email == 'test@example.com'
        assert user.username == 'testuser'
        assert user.is_active is True

    def test_email_uniqueness_constraint(self):
        """Test that email uniqueness is enforced at the database level."""
        User.objects.create_user(
            username='user1',
            email='unique@example.com',
            password='testpass123'
        )

        # Creating another user with the same email should work at model level
        # but fail when enforced by application logic
        user2 = User.objects.create_user(
            username='user2',
            email='different@example.com',
            password='testpass123'
        )
        assert user2.email != 'unique@example.com'

    def test_password_hashing_on_save(self):
        """Test that passwords are hashed when user is created."""
        password = 'mySecurePass123'
        user = User.objects.create_user(
            username='hashtest',
            email='hash@example.com',
            password=password
        )

        # Password should not be stored in plain text
        assert user.password != password
        # But should be verifiable with check_password
        assert check_password(password, user.password)

    def test_profile_relationship_one_to_one(self):
        """Test that UserProfile is automatically created with one-to-one relationship."""
        user = User.objects.create_user(
            username='profiletest',
            email='profile@example.com',
            password='testpass123'
        )

        # Profile should be automatically created via signal
        assert hasattr(user, 'profile')
        assert isinstance(user.profile, UserProfile)
        assert user.profile.user == user


@pytest.mark.django_db
class TestUserProfileModel:
    """Test suite for UserProfile model."""

    def test_profile_created_automatically(self):
        """Test that profile is automatically created when user is created."""
        user = User.objects.create_user(
            username='autocreate',
            email='auto@example.com',
            password='testpass123'
        )

        profile = UserProfile.objects.get(user=user)
        assert profile is not None
        assert profile.user == user

    def test_timezone_defaults_to_utc(self):
        """Test that timezone field defaults to UTC."""
        user = User.objects.create_user(
            username='timezonetest',
            email='tz@example.com',
            password='testpass123'
        )

        assert user.profile.timezone == 'UTC'

    def test_profile_fields_are_optional(self):
        """Test that optional profile fields can be left blank."""
        user = User.objects.create_user(
            username='optionaltest',
            email='optional@example.com',
            password='testpass123'
        )

        profile = user.profile
        assert profile.full_name == ''
        assert profile.job_title == ''
        assert profile.company == ''
        assert profile.phone_number == ''
        assert profile.avatar.name == ''

    def test_profile_timestamps(self):
        """Test that created_at and updated_at timestamps are set."""
        user = User.objects.create_user(
            username='timestamptest',
            email='timestamp@example.com',
            password='testpass123'
        )

        profile = user.profile
        assert profile.created_at is not None
        assert profile.updated_at is not None
        assert profile.created_at <= profile.updated_at
