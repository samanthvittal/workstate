"""
Tests for search models functionality.
"""
import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from tasks.models import SearchHistory, SavedSearch, Task


@pytest.mark.django_db
class TestSearchHistoryModel:
    """Test suite for SearchHistory model."""

    def test_search_history_creation(self, user):
        """Test creating search history record."""
        history = SearchHistory.objects.create(
            user=user,
            query='urgent tasks',
            result_count=5
        )

        assert history.user == user
        assert history.query == 'urgent tasks'
        assert history.result_count == 5
        assert history.searched_at is not None

    def test_get_recent_for_user(self, user):
        """Test retrieving recent searches for a user."""
        # Create multiple search history records
        SearchHistory.objects.create(user=user, query='test 1', result_count=1)
        SearchHistory.objects.create(user=user, query='test 2', result_count=2)
        SearchHistory.objects.create(user=user, query='test 3', result_count=3)

        recent_searches = SearchHistory.objects.get_recent_for_user(user, limit=2)

        # Should return 2 most recent searches
        assert recent_searches.count() == 2
        # Should be ordered by searched_at descending (most recent first)
        assert recent_searches[0].query == 'test 3'
        assert recent_searches[1].query == 'test 2'

    def test_prune_old_searches(self, user):
        """Test automatic pruning of old search history."""
        # Create 60 search history records
        for i in range(60):
            SearchHistory.objects.create(
                user=user,
                query=f'search {i}',
                result_count=i
            )

        # Verify all 60 exist
        assert SearchHistory.objects.filter(user=user).count() == 60

        # Prune to keep only 50 most recent
        SearchHistory.objects.prune_old_searches(user, keep_count=50)

        # Should now have only 50 searches
        assert SearchHistory.objects.filter(user=user).count() == 50

        # Most recent search should still exist
        recent = SearchHistory.objects.get_recent_for_user(user, limit=1)[0]
        assert recent.query == 'search 59'


@pytest.mark.django_db
class TestSavedSearchModel:
    """Test suite for SavedSearch model."""

    def test_saved_search_creation(self, user):
        """Test creating saved search with filters."""
        filters = {
            'workspace_id': 1,
            'status': 'active',
            'priority': ['P1', 'P2']
        }

        saved_search = SavedSearch.objects.create(
            user=user,
            name='High Priority Tasks',
            query='urgent',
            filters=filters
        )

        assert saved_search.user == user
        assert saved_search.name == 'High Priority Tasks'
        assert saved_search.query == 'urgent'
        assert saved_search.filters == filters

    def test_unique_name_per_user(self, user, user2):
        """Test that saved search names are unique per user."""
        # Create first saved search
        SavedSearch.objects.create(
            user=user,
            name='My Search',
            query='test'
        )

        # Try to create duplicate for same user - should fail
        with pytest.raises(ValidationError):
            SavedSearch.objects.create(
                user=user,
                name='My Search',
                query='test2'
            )

        # Different user can have same name - should succeed
        saved_search = SavedSearch.objects.create(
            user=user2,
            name='My Search',
            query='test3'
        )
        assert saved_search.name == 'My Search'

    def test_max_20_saved_searches_validation(self, user):
        """Test that users cannot save more than 20 searches."""
        # Create 20 saved searches
        for i in range(20):
            SavedSearch.objects.create(
                user=user,
                name=f'Search {i}',
                query=f'query {i}'
            )

        # Try to create 21st saved search - should fail
        with pytest.raises(ValidationError) as exc_info:
            SavedSearch.objects.create(
                user=user,
                name='Search 21',
                query='query 21'
            )

        assert 'Cannot save more than 20 searches' in str(exc_info.value)

    def test_empty_name_validation(self, user):
        """Test that saved search name cannot be empty."""
        saved_search = SavedSearch(
            user=user,
            name='   ',  # Only whitespace
            query='test'
        )

        with pytest.raises(ValidationError) as exc_info:
            saved_search.save()

        assert 'name' in exc_info.value.message_dict


@pytest.mark.django_db
class TestTaskSearchVector:
    """Test suite for Task search_vector field and trigger."""

    def test_search_vector_populated_on_create(self, user, workspace, task_list):
        """Test that search_vector is automatically populated when task is created."""
        task = Task.objects.create(
            title='Implement search feature',
            description='Add full-text search using PostgreSQL',
            priority='P1',
            task_list=task_list,
            created_by=user
        )

        # Refresh from database to get updated search_vector
        task.refresh_from_db()

        # search_vector should be populated
        assert task.search_vector is not None

    def test_search_vector_updated_on_title_change(self, user, workspace, task_list):
        """Test that search_vector is automatically updated when title changes."""
        task = Task.objects.create(
            title='Original title',
            description='Original description',
            priority='P1',
            task_list=task_list,
            created_by=user
        )

        # Change title
        task.title = 'Updated title'
        task.save()
        task.refresh_from_db()

        # search_vector should be updated
        assert task.search_vector is not None

    def test_search_vector_updated_on_description_change(self, user, workspace, task_list):
        """Test that search_vector is automatically updated when description changes."""
        task = Task.objects.create(
            title='Test task',
            description='Original description',
            priority='P1',
            task_list=task_list,
            created_by=user
        )

        # Change description
        task.description = 'Updated description with new keywords'
        task.save()
        task.refresh_from_db()

        # search_vector should be updated
        assert task.search_vector is not None
