"""
Tests for Workspace model and constellation name generator.
"""
import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError
from accounts.models import Workspace
from accounts.utils import ConstellationNameGenerator, generate_constellation_name


@pytest.mark.django_db
class TestWorkspaceModel:
    """Test suite for Workspace model."""

    def test_workspace_creation_with_user(self):
        """Test that a workspace can be created with a user."""
        user = User.objects.create_user(
            username='workspacetest',
            email='workspace@example.com',
            password='testpass123'
        )

        workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=user,
            is_personal=True
        )

        assert workspace.id is not None
        assert workspace.name == 'Test Workspace'
        assert workspace.owner == user
        assert workspace.is_personal is True
        assert workspace.created_at is not None
        assert workspace.updated_at is not None

    def test_workspace_name_uniqueness_per_user(self):
        """Test that workspace names must be unique per user."""
        user = User.objects.create_user(
            username='uniquetest',
            email='unique@example.com',
            password='testpass123'
        )

        # Create first workspace
        Workspace.objects.create(
            name='My Workspace',
            owner=user
        )

        # Attempting to create another workspace with same name for same user should fail
        with pytest.raises(IntegrityError):
            Workspace.objects.create(
                name='My Workspace',
                owner=user
            )

    def test_workspace_same_name_different_users(self):
        """Test that different users can have workspaces with the same name."""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )

        workspace1 = Workspace.objects.create(
            name='Shared Name',
            owner=user1
        )
        workspace2 = Workspace.objects.create(
            name='Shared Name',
            owner=user2
        )

        assert workspace1.name == workspace2.name
        assert workspace1.owner != workspace2.owner

    def test_workspace_user_relationship(self):
        """Test that workspace-user relationship is properly established."""
        user = User.objects.create_user(
            username='relationtest',
            email='relation@example.com',
            password='testpass123'
        )

        workspace1 = Workspace.objects.create(
            name='Workspace 1',
            owner=user
        )
        workspace2 = Workspace.objects.create(
            name='Workspace 2',
            owner=user
        )

        # User should have access to their workspaces via reverse relationship
        user_workspaces = user.workspaces.all()
        assert user_workspaces.count() == 2
        assert workspace1 in user_workspaces
        assert workspace2 in user_workspaces

    def test_workspace_cascade_delete(self):
        """Test that workspaces are deleted when user is deleted."""
        user = User.objects.create_user(
            username='cascadetest',
            email='cascade@example.com',
            password='testpass123'
        )

        Workspace.objects.create(name='Workspace 1', owner=user)
        Workspace.objects.create(name='Workspace 2', owner=user)

        workspace_count_before = Workspace.objects.filter(owner=user).count()
        assert workspace_count_before == 2

        # Delete user
        user.delete()

        # Workspaces should be deleted as well
        workspace_count_after = Workspace.objects.filter(owner__email='cascade@example.com').count()
        assert workspace_count_after == 0


@pytest.mark.django_db
class TestConstellationNameGenerator:
    """Test suite for ConstellationNameGenerator utility."""

    def test_generate_returns_constellation_name(self):
        """Test that generate() returns a valid constellation name."""
        name = ConstellationNameGenerator.generate()

        assert name in ConstellationNameGenerator.CONSTELLATION_NAMES
        assert isinstance(name, str)
        assert len(name) > 0

    def test_generate_is_random(self):
        """Test that multiple calls to generate() can produce different names."""
        # Generate 20 names and check if we get at least 2 different ones
        # This tests randomness without being flaky
        names = [ConstellationNameGenerator.generate() for _ in range(20)]
        unique_names = set(names)

        # With 20 tries and 10 possible names, we should get multiple unique names
        assert len(unique_names) >= 2

    def test_generate_unique_with_no_existing_names(self):
        """Test that generate_unique() returns a constellation name when no names exist."""
        name = ConstellationNameGenerator.generate_unique([])

        assert name in ConstellationNameGenerator.CONSTELLATION_NAMES

    def test_generate_unique_avoids_existing_names(self):
        """Test that generate_unique() avoids names in the existing list."""
        existing = ['Orion', 'Andromeda', 'Cassiopeia']
        name = ConstellationNameGenerator.generate_unique(existing)

        # Should return a name not in the existing list
        if name in ConstellationNameGenerator.CONSTELLATION_NAMES:
            assert name not in existing
        else:
            # If all base names are taken, it should have a numeric suffix
            assert any(base in name for base in ConstellationNameGenerator.CONSTELLATION_NAMES)

    def test_generate_unique_adds_numeric_suffix_when_all_taken(self):
        """Test that generate_unique() adds numeric suffix when all base names are taken."""
        # Use all constellation names
        existing = ConstellationNameGenerator.CONSTELLATION_NAMES.copy()
        name = ConstellationNameGenerator.generate_unique(existing)

        # Should have a numeric suffix
        assert any(name.startswith(base) for base in ConstellationNameGenerator.CONSTELLATION_NAMES)
        assert name not in existing

    def test_utility_function_generate_constellation_name(self):
        """Test the utility function generate_constellation_name()."""
        # Without user
        name = generate_constellation_name()
        assert name in ConstellationNameGenerator.CONSTELLATION_NAMES

        # With user
        user = User.objects.create_user(
            username='consttest',
            email='const@example.com',
            password='testpass123'
        )

        # Create some workspaces
        Workspace.objects.create(name='Orion', owner=user)
        Workspace.objects.create(name='Andromeda', owner=user)

        # Generate should avoid existing names
        new_name = generate_constellation_name(user)
        existing_names = ['Orion', 'Andromeda']

        if new_name in ConstellationNameGenerator.CONSTELLATION_NAMES:
            assert new_name not in existing_names
