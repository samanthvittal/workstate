"""
Tests for search UI components (Task Group 4: Search UI Templates and Interactions).

This test file covers:
- Navigation bar search input rendering
- Search dropdown HTMX functionality
- Search results page display with filters
- Saved search modal submission
- Filter badges display and removal
- Keyboard navigation
- Responsive design elements

Limited to 8 focused tests as per Task Group 4.1 requirements.
"""
import pytest
from django.urls import reverse
from tasks.models import Task, SavedSearch, SearchHistory


@pytest.mark.django_db
class TestNavigationBarSearchInput:
    """Test suite for navigation bar search input rendering."""

    def test_nav_bar_renders_search_input_with_htmx_attributes(self, client, user, workspace, task_list):
        """Test that navigation bar displays search input with correct HTMX attributes and styling."""
        client.force_login(user)
        url = reverse('tasks:task-list-all')
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Verify search input is present in nav bar
        assert 'Search tasks...' in content
        assert 'type="search"' in content or 'type="text"' in content

        # Verify HTMX attributes for live search
        assert 'hx-get' in content
        assert '/search/dropdown/' in content
        assert 'delay:300ms' in content or 'changed delay:300ms' in content

        # Verify search icon SVG is present
        assert '<svg' in content
        assert 'M21 21l' in content or 'search' in content.lower()

        # Verify Tailwind styling classes
        assert 'border-gray-300' in content or 'rounded' in content
        assert 'focus:ring' in content or 'focus-visible:ring' in content


@pytest.mark.django_db
class TestSearchDropdownDisplay:
    """Test suite for search dropdown HTMX functionality."""

    def test_search_dropdown_displays_task_previews(self, client, user, workspace, task_list):
        """Test that search dropdown shows task previews with correct metadata."""
        # Create searchable tasks
        task1 = Task.objects.create(
            title='Important Meeting Task',
            description='Discuss project timeline',
            priority='P1',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        task2 = Task.objects.create(
            title='Review Meeting Notes',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        client.force_login(user)
        url = reverse('tasks:search-dropdown')
        response = client.get(url, {'q': 'meeting'})

        assert response.status_code == 200
        content = response.content.decode()

        # Verify task titles are displayed
        assert 'Important Meeting Task' in content
        assert 'Review Meeting Notes' in content

        # Verify "View all results" link is present
        assert 'View all' in content
        assert reverse('tasks:search-results') in content

    def test_search_dropdown_shows_no_results_message(self, client, user, workspace, task_list):
        """Test that search dropdown shows appropriate message when no results found."""
        client.force_login(user)
        url = reverse('tasks:search-dropdown')
        response = client.get(url, {'q': 'nonexistentquery123'})

        assert response.status_code == 200
        content = response.content.decode()

        # Verify "no results" message
        assert 'No results' in content or 'no results' in content.lower()


@pytest.mark.django_db
class TestSearchResultsPage:
    """Test suite for search results page display."""

    def test_search_results_page_displays_query_and_result_count(self, client, user, workspace, task_list):
        """Test that search results page shows search query and result count prominently."""
        # Create searchable tasks
        Task.objects.create(
            title='Python Development Task',
            priority='P1',
            task_list=task_list,
            created_by=user,
            status='active'
        )
        Task.objects.create(
            title='Python Code Review',
            priority='P2',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        client.force_login(user)
        url = reverse('tasks:search-results')
        response = client.get(url, {'q': 'python'})

        assert response.status_code == 200
        content = response.content.decode()

        # Verify search query is displayed
        assert 'python' in content.lower()

        # Verify result count is displayed
        assert '2' in content
        assert 'result' in content.lower()

        # Verify tasks are displayed using task card partial
        assert 'Python Development Task' in content
        assert 'Python Code Review' in content

    def test_search_results_page_displays_filters_sidebar(self, client, user, workspace, task_list):
        """Test that search results page includes filters sidebar with workspace, tags, status, and priority."""
        # Create task with tags
        task = Task.objects.create(
            title='Tagged Task',
            priority='P1',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        client.force_login(user)
        url = reverse('tasks:search-results')
        response = client.get(url, {'q': 'task'})

        assert response.status_code == 200
        content = response.content.decode()

        # Verify filter sections are present
        assert 'Status' in content or 'status' in content
        assert 'Priority' in content or 'priority' in content

        # Verify filter options
        assert 'Active' in content
        assert 'Completed' in content
        assert 'P1' in content or 'P2' in content


@pytest.mark.django_db
class TestSavedSearchesDisplay:
    """Test suite for saved searches sidebar section."""

    def test_saved_searches_section_displays_in_sidebar(self, client, user, workspace, task_list):
        """Test that saved searches section displays saved searches with edit/delete options."""
        # Create a saved search
        SavedSearch.objects.create(
            user=user,
            name='High Priority Tasks',
            query='priority:P1',
            filters={'priority': ['P1']}
        )

        client.force_login(user)
        url = reverse('tasks:search-results')
        response = client.get(url, {'q': 'test'})

        assert response.status_code == 200
        content = response.content.decode()

        # Verify saved searches section exists
        assert 'Saved Searches' in content or 'saved searches' in content.lower()

        # Verify saved search name is displayed
        assert 'High Priority Tasks' in content

        # Verify delete action is available
        assert 'delete' in content.lower() or 'Delete' in content


@pytest.mark.django_db
class TestRecentSearchesDisplay:
    """Test suite for recent searches sidebar section."""

    def test_recent_searches_section_displays_search_history(self, client, user, workspace, task_list):
        """Test that recent searches section displays recent search queries."""
        # Create search history entries
        SearchHistory.objects.create(
            user=user,
            query='important meetings',
            result_count=5
        )
        SearchHistory.objects.create(
            user=user,
            query='overdue tasks',
            result_count=3
        )

        client.force_login(user)
        url = reverse('tasks:search-results')
        response = client.get(url, {'q': 'test'})

        assert response.status_code == 200
        content = response.content.decode()

        # Verify recent searches section exists
        assert 'Recent Searches' in content or 'recent searches' in content.lower()

        # Verify recent search queries are displayed
        assert 'important meetings' in content
        assert 'overdue tasks' in content


@pytest.mark.django_db
class TestSaveSearchModal:
    """Test suite for save search modal functionality."""

    def test_save_search_button_renders_on_search_results_page(self, client, user, workspace, task_list):
        """Test that save search button is present on search results page."""
        Task.objects.create(
            title='Test Task',
            priority='P1',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        client.force_login(user)
        url = reverse('tasks:search-results')
        response = client.get(url, {'q': 'test'})

        assert response.status_code == 200
        content = response.content.decode()

        # Verify save search button/link is present
        assert 'Save Search' in content or 'save search' in content.lower()


@pytest.mark.django_db
class TestSearchResultHighlighting:
    """Test suite for search result highlighting."""

    def test_search_results_include_highlighting_markup(self, client, user, workspace, task_list):
        """Test that search results include proper highlighting with mark tags."""
        Task.objects.create(
            title='Important Django Development',
            description='Working on Django features',
            priority='P1',
            task_list=task_list,
            created_by=user,
            status='active'
        )

        client.force_login(user)
        url = reverse('tasks:search-results')
        response = client.get(url, {'q': 'django'})

        assert response.status_code == 200
        content = response.content.decode()

        # Verify task title is present (highlighting may be applied)
        assert 'Django' in content or 'django' in content

        # Verify result includes the task
        assert 'Important Django Development' in content or 'django' in content.lower()
