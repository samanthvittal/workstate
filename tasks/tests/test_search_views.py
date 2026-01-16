"""
Tests for search views.

Tests cover critical functionality:
- Authentication and permission enforcement
- Search dropdown returns preview results
- Search results page displays paginated results
- Saved search creation and deletion
- Search history recording and clearing
"""
import pytest
from django.urls import reverse
from tasks.models import Task, SavedSearch, SearchHistory


@pytest.mark.django_db
class TestSearchDropdownView:
    """Test suite for SearchDropdownView."""

    def test_search_dropdown_requires_authentication(self, client):
        """Test that SearchDropdownView requires authentication."""
        url = reverse('tasks:search-dropdown')
        response = client.get(url, {'q': 'test'})

        # Should redirect to login page
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_search_dropdown_returns_preview_results(self, client, user, task_list, task):
        """Test that search dropdown returns up to 5 preview results."""
        client.force_login(user)

        # Create tasks with searchable content
        for i in range(7):
            Task.objects.create(
                title=f'Meeting task {i}',
                description='Important meeting notes',
                priority='P2',
                task_list=task_list,
                created_by=user
            )

        url = reverse('tasks:search-dropdown')
        response = client.get(url, {'q': 'meeting'})

        assert response.status_code == 200
        # Should return max 5 tasks in preview
        assert 'tasks' in response.context
        assert len(response.context['tasks']) == 5
        assert response.context['result_count'] == 7

    def test_search_dropdown_empty_query(self, client, user):
        """Test that empty query returns empty dropdown."""
        client.force_login(user)

        url = reverse('tasks:search-dropdown')
        response = client.get(url, {'q': ''})

        assert response.status_code == 200
        assert len(response.context['tasks']) == 0


@pytest.mark.django_db
class TestSearchResultsView:
    """Test suite for SearchResultsView."""

    def test_search_results_requires_authentication(self, client):
        """Test that SearchResultsView requires authentication."""
        url = reverse('tasks:search-results')
        response = client.get(url, {'q': 'test'})

        # Should redirect to login page
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_search_results_displays_paginated_results(self, client, user, task_list):
        """Test that search results page displays paginated results."""
        client.force_login(user)

        # Create 30 tasks with searchable content
        for i in range(30):
            Task.objects.create(
                title=f'Project task {i}',
                description='Project documentation',
                priority='P2',
                task_list=task_list,
                created_by=user
            )

        url = reverse('tasks:search-results')
        response = client.get(url, {'q': 'project'})

        assert response.status_code == 200
        # Should paginate at 25 per page
        assert len(response.context['tasks']) == 25
        assert response.context['result_count'] == 30
        assert response.context['query'] == 'project'

    def test_search_results_records_search_history(self, client, user, task_list, task):
        """Test that search results records search in history."""
        client.force_login(user)

        # Update task to have searchable content
        task.title = 'Bug fix needed'
        task.save()

        url = reverse('tasks:search-results')
        response = client.get(url, {'q': 'bug'})

        assert response.status_code == 200

        # Verify search was recorded in history
        history = SearchHistory.objects.filter(user=user, query='bug')
        assert history.exists()
        assert history.first().result_count > 0

    def test_search_results_permission_filtering(self, client, user, user2, task_list, task_list2):
        """Test that search results only show user's accessible tasks."""
        client.force_login(user)

        # Create tasks in both workspaces
        Task.objects.create(
            title='User1 confidential task',
            priority='P1',
            task_list=task_list,
            created_by=user
        )

        Task.objects.create(
            title='User2 confidential task',
            priority='P1',
            task_list=task_list2,
            created_by=user2
        )

        url = reverse('tasks:search-results')
        response = client.get(url, {'q': 'confidential'})

        assert response.status_code == 200
        # Should only return user's task, not user2's
        assert response.context['result_count'] == 1
        assert 'User1 confidential' in response.context['tasks'][0].title

    def test_search_results_with_filters(self, client, user, task_list):
        """Test that search results apply workspace and status filters."""
        client.force_login(user)

        # Create active and completed tasks
        active_task = Task.objects.create(
            title='Active search task',
            priority='P2',
            status='active',
            task_list=task_list,
            created_by=user
        )

        completed_task = Task.objects.create(
            title='Completed search task',
            priority='P2',
            status='completed',
            task_list=task_list,
            created_by=user
        )

        url = reverse('tasks:search-results')

        # Test status filter
        response = client.get(url, {'q': 'search', 'status': 'active'})
        assert response.status_code == 200
        assert response.context['result_count'] == 1

        response = client.get(url, {'q': 'search', 'status': 'all'})
        assert response.status_code == 200
        assert response.context['result_count'] == 2


@pytest.mark.django_db
class TestSaveSearchView:
    """Test suite for SaveSearchView."""

    def test_save_search_requires_authentication(self, client):
        """Test that SaveSearchView requires authentication."""
        url = reverse('tasks:search-save')
        response = client.post(url, {
            'name': 'My Search',
            'query': 'test'
        })

        # Should redirect to login page
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_save_search_creates_saved_search(self, client, user):
        """Test that save search creates SavedSearch record."""
        client.force_login(user)

        url = reverse('tasks:search-save')
        response = client.post(url, {
            'name': 'Important Tasks',
            'query': 'urgent',
            'status': 'active',
            'priority': ['P1', 'P2']
        })

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

        # Verify saved search was created
        saved_search = SavedSearch.objects.get(user=user, name='Important Tasks')
        assert saved_search.query == 'urgent'
        assert saved_search.filters['status'] == 'active'
        assert 'P1' in saved_search.filters['priority']

    def test_save_search_validation(self, client, user):
        """Test that save search validates required fields."""
        client.force_login(user)

        url = reverse('tasks:search-save')

        # Missing name
        response = client.post(url, {'query': 'test'})
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False

        # Missing query
        response = client.post(url, {'name': 'Test'})
        assert response.status_code == 400


@pytest.mark.django_db
class TestDeleteSearchView:
    """Test suite for DeleteSearchView."""

    def test_delete_search_requires_authentication(self, client, user):
        """Test that DeleteSearchView requires authentication."""
        saved_search = SavedSearch.objects.create(
            user=user,
            name='Test Search',
            query='test'
        )

        url = reverse('tasks:search-delete', kwargs={'pk': saved_search.id})
        response = client.post(url)

        # Should redirect to login page
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_delete_search_removes_saved_search(self, client, user):
        """Test that delete search removes SavedSearch record."""
        client.force_login(user)

        saved_search = SavedSearch.objects.create(
            user=user,
            name='Old Search',
            query='outdated'
        )

        url = reverse('tasks:search-delete', kwargs={'pk': saved_search.id})
        response = client.post(url)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

        # Verify saved search was deleted
        assert not SavedSearch.objects.filter(id=saved_search.id).exists()

    def test_delete_search_permission_check(self, client, user, user2):
        """Test that users cannot delete other users' saved searches."""
        client.force_login(user)

        # Create saved search for user2
        saved_search = SavedSearch.objects.create(
            user=user2,
            name='User2 Search',
            query='private'
        )

        url = reverse('tasks:search-delete', kwargs={'pk': saved_search.id})
        response = client.post(url)

        # Should return 403 Forbidden
        assert response.status_code == 403


@pytest.mark.django_db
class TestClearSearchHistoryView:
    """Test suite for ClearSearchHistoryView."""

    def test_clear_history_requires_authentication(self, client):
        """Test that ClearSearchHistoryView requires authentication."""
        url = reverse('tasks:search-history-clear')
        response = client.post(url)

        # Should redirect to login page
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_clear_history_removes_all_user_searches(self, client, user):
        """Test that clear history removes all search history for user."""
        client.force_login(user)

        # Create multiple search history entries
        for i in range(5):
            SearchHistory.objects.create(
                user=user,
                query=f'search {i}',
                result_count=10
            )

        url = reverse('tasks:search-history-clear')
        response = client.post(url)

        assert response.status_code == 200
        # View now returns HTML partial instead of JSON
        assert b'recent_searches' in response.content or b'No recent searches' in response.content

        # Verify all history was deleted
        assert SearchHistory.objects.filter(user=user).count() == 0

    def test_clear_history_only_clears_user_history(self, client, user, user2):
        """Test that clear history only removes current user's searches."""
        client.force_login(user)

        # Create search history for both users
        SearchHistory.objects.create(user=user, query='user1 search', result_count=5)
        SearchHistory.objects.create(user=user2, query='user2 search', result_count=5)

        url = reverse('tasks:search-history-clear')
        response = client.post(url)

        assert response.status_code == 200

        # User1's history should be cleared
        assert SearchHistory.objects.filter(user=user).count() == 0

        # User2's history should remain
        assert SearchHistory.objects.filter(user=user2).count() == 1
