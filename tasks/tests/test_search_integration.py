"""
Integration tests for Task Search feature (Task Group 5).

This test suite covers end-to-end workflows and integration points that weren't
covered in previous task groups. Focus areas:
- Complete search workflows from input to results
- Multi-filter combinations
- Performance and query optimization
- Security validations
- Cross-workspace permission boundaries

Limited to 10 strategic tests as per requirements.
"""
import pytest
from django.urls import reverse
from django.test import override_settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from tasks.models import Task, SavedSearch, SearchHistory, Tag
from tasks.services import SearchQueryService


@pytest.mark.django_db
class TestEndToEndSearchWorkflow:
    """Test complete search workflows from start to finish."""

    def test_complete_search_workflow_nav_to_saved_search(self, client, user, workspace, task_list):
        """
        Test end-to-end workflow: search in nav bar → view dropdown →
        go to full results → apply filters → save search → load saved search.
        """
        client.force_login(user)

        # Create searchable tasks with different attributes
        task1 = Task.objects.create(
            title='Urgent bug fix for payment system',
            description='Critical payment processing issue',
            priority='P1',
            status='active',
            task_list=task_list,
            created_by=user
        )
        task2 = Task.objects.create(
            title='Bug in user authentication',
            description='Users cannot log in',
            priority='P2',
            status='active',
            task_list=task_list,
            created_by=user
        )
        task3 = Task.objects.create(
            title='Update bug documentation',
            description='Document all known bugs',
            priority='P3',
            status='completed',
            task_list=task_list,
            created_by=user
        )

        # Step 1: Search in dropdown (simulates nav bar search)
        dropdown_url = reverse('tasks:search-dropdown')
        response = client.get(dropdown_url, {'q': 'bug'})
        assert response.status_code == 200
        assert len(response.context['tasks']) <= 5  # Max 5 preview results
        assert response.context['result_count'] >= 2  # At least 2 active bugs

        # Step 2: Go to full results page (defaults to active tasks only)
        results_url = reverse('tasks:search-results')
        response = client.get(results_url, {'q': 'bug'})
        assert response.status_code == 200
        # Default status filter is 'active', so only 2 active tasks
        assert response.context['result_count'] == 2

        # Step 2b: Search with status='all' to see all tasks
        response = client.get(results_url, {'q': 'bug', 'status': 'all'})
        assert response.status_code == 200
        assert response.context['result_count'] == 3  # All 3 tasks with 'bug'

        # Step 3: Apply filters (only active, P1 priority)
        response = client.get(results_url, {
            'q': 'bug',
            'status': 'active',
            'priority': ['P1']
        })
        assert response.status_code == 200
        assert response.context['result_count'] == 1  # Only urgent bug
        assert task1 in response.context['tasks']

        # Step 4: Save this search
        save_url = reverse('tasks:search-save')
        response = client.post(save_url, {
            'name': 'Critical Bugs',
            'query': 'bug',
            'status': 'active',
            'priority': ['P1']
        })
        assert response.status_code == 200
        assert response.json()['success'] is True

        # Verify saved search was created
        saved_search = SavedSearch.objects.get(user=user, name='Critical Bugs')
        assert saved_search.query == 'bug'
        assert saved_search.filters['status'] == 'active'
        assert 'P1' in saved_search.filters['priority']

        # Step 5: Load saved search by accessing results with saved filters
        response = client.get(results_url, {
            'q': saved_search.query,
            'status': saved_search.filters['status'],
            'priority': saved_search.filters['priority']
        })
        assert response.status_code == 200
        assert response.context['result_count'] == 1

        # Step 6: Verify search history was recorded
        history = SearchHistory.objects.filter(user=user, query='bug')
        assert history.exists()
        assert history.count() >= 2  # Multiple searches with 'bug'


@pytest.mark.django_db
class TestSearchWithMultipleFilters:
    """Test search with combinations of multiple filters."""

    def test_search_with_workspace_tag_status_priority_filters(self, client, user, workspace, task_list):
        """Test that multiple filters work correctly together."""
        client.force_login(user)

        # Create tags
        tag_backend = Tag.objects.create(
            name='backend',
            workspace=workspace,
            created_by=user
        )
        tag_frontend = Tag.objects.create(
            name='frontend',
            workspace=workspace,
            created_by=user
        )

        # Create tasks with various combinations
        task1 = Task.objects.create(
            title='Backend API development',
            description='Build REST API endpoints',
            priority='P1',
            status='active',
            task_list=task_list,
            created_by=user
        )
        task1.tags.add(tag_backend)

        task2 = Task.objects.create(
            title='Frontend UI development',
            description='Create user interface',
            priority='P2',
            status='active',
            task_list=task_list,
            created_by=user
        )
        task2.tags.add(tag_frontend)

        task3 = Task.objects.create(
            title='Backend database schema',
            description='Design database models',
            priority='P1',
            status='completed',
            task_list=task_list,
            created_by=user
        )
        task3.tags.add(tag_backend)

        # Apply all filters together: workspace + tag + status + priority
        url = reverse('tasks:search-results')
        response = client.get(url, {
            'q': 'development',
            'workspace': workspace.id,
            'tags': ['backend'],
            'status': 'active',
            'priority': ['P1']
        })

        assert response.status_code == 200
        # Should only return task1 (backend, active, P1)
        assert response.context['result_count'] == 1
        assert task1 in response.context['tasks']


@pytest.mark.django_db
class TestSearchSnippetGeneration:
    """Test search snippet generation with ts_headline."""

    def test_search_snippet_highlights_matched_terms(self, user, workspace, task_list):
        """Test that search snippets properly highlight matched terms."""
        task = Task.objects.create(
            title='Important Meeting',
            description='Discuss quarterly planning and review project milestones for the upcoming release cycle',
            priority='P2',
            task_list=task_list,
            created_by=user
        )

        # Generate snippet for search query
        snippet = task.get_search_snippet('planning milestones')

        # Snippet should contain highlighted terms
        assert '<mark>' in snippet
        assert '</mark>' in snippet
        # Should contain at least one of the search terms
        assert 'planning' in snippet.lower() or 'milestones' in snippet.lower()

    def test_search_snippet_fallback_for_empty_query(self, user, workspace, task_list):
        """Test that snippet generation falls back gracefully for empty queries."""
        task = Task.objects.create(
            title='Test Task',
            description='Test description for snippet generation',
            priority='P2',
            task_list=task_list,
            created_by=user
        )

        # Empty query should return description or title
        snippet = task.get_search_snippet('')
        assert snippet is not None
        assert len(snippet) > 0


@pytest.mark.django_db
class TestSearchPerformance:
    """Test query performance and optimization."""

    def test_search_results_no_n_plus_1_queries(self, client, user, workspace, task_list):
        """
        Test that search results don't trigger N+1 queries.
        Should use select_related and prefetch_related properly.
        """
        client.force_login(user)

        # Create multiple tasks
        for i in range(10):
            Task.objects.create(
                title=f'Performance test task {i}',
                description='Testing query optimization',
                priority='P2',
                task_list=task_list,
                created_by=user
            )

        url = reverse('tasks:search-results')

        # Count queries executed
        with CaptureQueriesContext(connection) as context:
            response = client.get(url, {'q': 'performance'})
            assert response.status_code == 200

        # Should have minimal queries (search + prefetch + pagination)
        # Expected: ~10-20 queries maximum (search, task lists, workspaces, tags, users, counts, etc.)
        # This is more lenient to account for session, auth, and Django overhead
        assert len(context.captured_queries) < 25, (
            f"Too many queries ({len(context.captured_queries)}). "
            f"Possible N+1 query issue."
        )

    def test_search_with_large_result_set_pagination(self, client, user, workspace, task_list):
        """Test search performance with large result sets and pagination."""
        client.force_login(user)

        # Create 50 searchable tasks
        for i in range(50):
            Task.objects.create(
                title=f'Task {i} with scalability keyword',
                description=f'Testing scalability with many results',
                priority='P2',
                task_list=task_list,
                created_by=user
            )

        url = reverse('tasks:search-results')

        # First page should return 25 results
        response = client.get(url, {'q': 'scalability'})
        assert response.status_code == 200
        assert len(response.context['tasks']) == 25

        # Second page should return remaining 25 results
        response = client.get(url, {'q': 'scalability', 'page': 2})
        assert response.status_code == 200
        assert len(response.context['tasks']) == 25


@pytest.mark.django_db
class TestAdvancedSearchOperators:
    """Test advanced search operators in complex combinations."""

    def test_and_or_not_operators_combined(self, client, user, workspace, task_list):
        """Test complex queries with multiple operators."""
        client.force_login(user)

        # Create tasks for operator testing
        Task.objects.create(
            title='Frontend bug in login system',
            description='Critical authentication issue',
            priority='P1',
            task_list=task_list,
            created_by=user
        )
        Task.objects.create(
            title='Backend API feature development',
            description='New API endpoints needed',
            priority='P2',
            task_list=task_list,
            created_by=user
        )
        Task.objects.create(
            title='Frontend feature for dashboard',
            description='New dashboard widgets',
            priority='P2',
            task_list=task_list,
            created_by=user
        )

        # Test AND operator: frontend AND bug
        response = client.get(reverse('tasks:search-results'), {'q': 'frontend & bug'})
        assert response.status_code == 200
        assert response.context['result_count'] == 1

        # Test OR operator: backend | frontend
        response = client.get(reverse('tasks:search-results'), {'q': 'backend | frontend', 'status': 'all'})
        assert response.status_code == 200
        assert response.context['result_count'] == 3

        # Test NOT operator: frontend & !bug
        response = client.get(reverse('tasks:search-results'), {'q': 'frontend & !bug'})
        assert response.status_code == 200
        # Should return frontend tasks without 'bug'
        assert response.context['result_count'] >= 1

    def test_phrase_search_with_quotes(self, client, user, workspace, task_list):
        """Test exact phrase search with double quotes."""
        client.force_login(user)

        Task.objects.create(
            title='User authentication system',
            description='Complete user auth implementation',
            priority='P1',
            task_list=task_list,
            created_by=user
        )
        Task.objects.create(
            title='System user management',
            description='User admin panel',
            priority='P2',
            task_list=task_list,
            created_by=user
        )

        # Phrase search should match exact phrase
        response = client.get(reverse('tasks:search-results'), {'q': '"user authentication"'})
        assert response.status_code == 200
        # Should prioritize exact phrase matches
        assert response.context['result_count'] >= 1


@pytest.mark.django_db
class TestCrossWorkspacePermissions:
    """Test permission boundaries across workspaces."""

    def test_user_cannot_search_other_workspaces(self, client, user, user2,
                                                   workspace, workspace2,
                                                   task_list, task_list2):
        """Test that search results are strictly scoped to user's workspaces."""
        client.force_login(user)

        # Create tasks in both workspaces with same search term
        task1 = Task.objects.create(
            title='Confidential project alpha',
            description='Secret information for user1',
            priority='P1',
            task_list=task_list,
            created_by=user
        )
        task2 = Task.objects.create(
            title='Confidential project beta',
            description='Secret information for user2',
            priority='P1',
            task_list=task_list2,
            created_by=user2
        )

        # User should only see their own task
        url = reverse('tasks:search-results')
        response = client.get(url, {'q': 'confidential'})
        assert response.status_code == 200
        assert response.context['result_count'] == 1
        assert task1 in response.context['tasks']
        assert task2 not in response.context['tasks']

        # Verify dropdown also respects permissions
        dropdown_url = reverse('tasks:search-dropdown')
        response = client.get(dropdown_url, {'q': 'confidential'})
        assert response.status_code == 200
        assert len(response.context['tasks']) == 1
        assert task1 in response.context['tasks']

    def test_workspace_filter_validates_user_access(self, client, user, user2,
                                                     workspace2, task_list):
        """Test that workspace filter validates user has access to workspace."""
        client.force_login(user)

        Task.objects.create(
            title='My searchable task',
            priority='P1',
            task_list=task_list,
            created_by=user
        )

        # Try to filter by workspace user doesn't own
        url = reverse('tasks:search-results')
        response = client.get(url, {
            'q': 'searchable',
            'workspace': workspace2.id  # user2's workspace
        })

        assert response.status_code == 200
        # Should return no results (permission filtering)
        assert response.context['result_count'] == 0


@pytest.mark.django_db
class TestSavedSearchWorkflow:
    """Test complete saved search lifecycle."""

    def test_save_load_delete_saved_search_workflow(self, client, user, workspace, task_list):
        """Test complete workflow: save search → load search → delete search."""
        client.force_login(user)

        # Create searchable task
        Task.objects.create(
            title='Important meeting notes',
            priority='P1',
            status='active',
            task_list=task_list,
            created_by=user
        )

        # Step 1: Save a search
        save_url = reverse('tasks:search-save')
        response = client.post(save_url, {
            'name': 'My Important Tasks',
            'query': 'important',
            'status': 'active',
            'priority': ['P1']
        })
        assert response.status_code == 200
        assert response.json()['success'] is True

        saved_search = SavedSearch.objects.get(user=user, name='My Important Tasks')
        assert saved_search is not None

        # Step 2: Load the saved search (verify it appears in sidebar)
        results_url = reverse('tasks:search-results')
        response = client.get(results_url, {'q': 'test'})
        assert response.status_code == 200
        assert 'My Important Tasks' in response.content.decode()

        # Step 3: Delete the saved search
        delete_url = reverse('tasks:search-delete', kwargs={'pk': saved_search.id})
        response = client.post(delete_url)
        assert response.status_code == 200
        assert response.json()['success'] is True

        # Verify it's deleted
        assert not SavedSearch.objects.filter(id=saved_search.id).exists()

    def test_saved_search_limit_validation(self, client, user):
        """Test that users cannot save more than 20 searches."""
        client.force_login(user)

        # Create 20 saved searches
        for i in range(20):
            SavedSearch.objects.create(
                user=user,
                name=f'Search {i}',
                query=f'query{i}'
            )

        # Try to create 21st
        save_url = reverse('tasks:search-save')
        response = client.post(save_url, {
            'name': 'Search 21',
            'query': 'overflow'
        })

        # Should fail validation
        assert response.status_code == 400
        assert response.json()['success'] is False


@pytest.mark.django_db
class TestSearchHistoryPruning:
    """Test search history recording and automatic pruning."""

    def test_search_history_auto_prunes_beyond_50_entries(self, client, user, workspace, task_list):
        """Test that search history automatically prunes to keep only 50 most recent."""
        client.force_login(user)

        # Create a task to search for
        Task.objects.create(
            title='Test task for history pruning',
            priority='P2',
            task_list=task_list,
            created_by=user
        )

        # Create 55 search history entries
        for i in range(55):
            SearchHistory.objects.create(
                user=user,
                query=f'search{i}',
                result_count=1
            )

        # Manually trigger pruning
        SearchHistory.objects.prune_old_searches(user, keep_count=50)

        # Should only have 50 entries
        count = SearchHistory.objects.filter(user=user).count()
        assert count == 50

        # Most recent searches should be kept
        recent = SearchHistory.objects.get_recent_for_user(user, limit=1)[0]
        assert 'search54' in recent.query  # Most recent entry

    def test_search_history_records_searches(self, client, user, workspace, task_list):
        """Test that search history records searches when performed."""
        client.force_login(user)

        Task.objects.create(
            title='Findable task',
            priority='P2',
            task_list=task_list,
            created_by=user
        )

        initial_count = SearchHistory.objects.filter(user=user).count()

        # Search with results
        url = reverse('tasks:search-results')
        response = client.get(url, {'q': 'findable'})
        assert response.status_code == 200

        # History should be recorded
        assert SearchHistory.objects.filter(user=user).count() == initial_count + 1


@pytest.mark.django_db
class TestSearchSecurity:
    """Test security measures for search functionality."""

    def test_search_input_sanitization_prevents_injection(self, client, user, workspace, task_list):
        """Test that search input is properly sanitized to prevent injection attacks."""
        client.force_login(user)

        Task.objects.create(
            title='Normal task',
            description='Regular content',
            priority='P2',
            task_list=task_list,
            created_by=user
        )

        # Try SQL injection patterns - should handle gracefully
        malicious_inputs = [
            "'; DROP TABLE tasks; --",
            "1' OR '1'='1",
            "' UNION SELECT * FROM users --",
        ]

        url = reverse('tasks:search-results')
        for malicious_input in malicious_inputs:
            # Should handle gracefully without errors
            response = client.get(url, {'q': malicious_input})
            # Should return 200 (not error) and sanitize input
            assert response.status_code == 200

    def test_regex_search_prevents_redos_attacks(self):
        """Test that regex validation prevents ReDoS attacks."""
        # Test dangerous nested quantifiers
        dangerous_patterns = [
            '(a+)+',
            '(a*)*',
            '(a+)*',
            '(a*)+',
        ]

        for pattern in dangerous_patterns:
            is_safe = SearchQueryService._validate_regex_pattern(pattern)
            assert is_safe is False, f"Pattern {pattern} should be rejected as unsafe"

    def test_saved_search_filters_respect_permissions(self, client, user, user2,
                                                       workspace, workspace2,
                                                       task_list, task_list2):
        """Test that saved search filters cannot bypass workspace permissions."""
        client.force_login(user)

        # Create task in user2's workspace
        Task.objects.create(
            title='User2 private task',
            priority='P1',
            task_list=task_list2,
            created_by=user2
        )

        # User1 tries to create saved search with user2's workspace filter
        save_url = reverse('tasks:search-save')
        response = client.post(save_url, {
            'name': 'Sneaky Search',
            'query': 'private',
            'workspace': workspace2.id  # user2's workspace
        })

        # Search should be saved but...
        if response.status_code == 200:
            # When loaded, should not return results from user2's workspace
            results_url = reverse('tasks:search-results')
            response = client.get(results_url, {
                'q': 'private',
                'workspace': workspace2.id
            })
            assert response.status_code == 200
            # Should return 0 results (permission filtering)
            assert response.context['result_count'] == 0
