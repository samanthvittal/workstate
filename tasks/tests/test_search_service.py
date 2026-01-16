"""
Tests for search service and manager methods.
"""
import pytest
from datetime import date, timedelta
from django.contrib.auth.models import User
from tasks.models import Task, Tag
from tasks.services import SearchQueryService


@pytest.mark.django_db
class TestSearchQueryService:
    """Test suite for SearchQueryService parsing and sanitization."""

    def test_parse_simple_query(self):
        """Test parsing simple search query."""
        result = SearchQueryService.parse_search_query('urgent tasks')
        assert result == 'urgent & tasks'

    def test_parse_and_operator(self):
        """Test parsing AND operator."""
        result1 = SearchQueryService.parse_search_query('bug AND feature')
        assert result1 == 'bug & feature'

        result2 = SearchQueryService.parse_search_query('bug & feature')
        assert result2 == 'bug & feature'

    def test_parse_or_operator(self):
        """Test parsing OR operator."""
        result1 = SearchQueryService.parse_search_query('bug OR feature')
        assert result1 == 'bug | feature'

        result2 = SearchQueryService.parse_search_query('bug | feature')
        assert result2 == 'bug | feature'

    def test_parse_not_operator(self):
        """Test parsing NOT operator."""
        # NOT as a word should be converted to !
        result1 = SearchQueryService.parse_search_query('NOT completed')
        assert result1 == '! completed'

        # ! prefix should be tokenized with space
        result2 = SearchQueryService.parse_search_query('!completed')
        # The tokenizer splits on operators, so '!completed' becomes '!' 'completed'
        assert '!' in result2 and 'completed' in result2

    def test_parse_phrase_search(self):
        """Test parsing phrase search with quotes."""
        result = SearchQueryService.parse_search_query('"exact match phrase"')
        assert result == "'exact match phrase'"

    def test_sanitize_dangerous_input(self):
        """Test that dangerous characters are sanitized."""
        result = SearchQueryService.parse_search_query('task<script>')
        assert '<script>' not in result
        assert 'taskscript' in result or 'task' in result

    def test_empty_query_returns_none(self):
        """Test that empty queries return None."""
        assert SearchQueryService.parse_search_query('') is None
        assert SearchQueryService.parse_search_query('   ') is None

    def test_validate_regex_pattern_safe(self):
        """Test regex pattern validation accepts safe patterns."""
        # Simple patterns should be accepted
        assert SearchQueryService._validate_regex_pattern(r'^test$') is True
        assert SearchQueryService._validate_regex_pattern(r'test\d+') is True

    def test_validate_regex_pattern_dangerous(self):
        """Test regex pattern validation rejects dangerous patterns."""
        # Nested quantifiers are dangerous
        assert SearchQueryService._validate_regex_pattern(r'(a+)+') is False
        assert SearchQueryService._validate_regex_pattern(r'(a*)*') is False


@pytest.mark.django_db
class TestTaskManagerSearch:
    """Test suite for TaskManager search methods."""

    def test_search_tasks_basic(self, user, workspace, task_list):
        """Test basic full-text search functionality."""
        # Create tasks with different content
        task1 = Task.objects.create(
            title='Fix urgent bug in payment system',
            description='Critical issue affecting users',
            priority='P1',
            task_list=task_list,
            created_by=user
        )
        task2 = Task.objects.create(
            title='Add new feature to dashboard',
            description='Implement user analytics',
            priority='P2',
            task_list=task_list,
            created_by=user
        )
        task3 = Task.objects.create(
            title='Update documentation',
            description='Add API reference docs',
            priority='P3',
            task_list=task_list,
            created_by=user
        )

        # Refresh to ensure search_vector is populated
        for task in [task1, task2, task3]:
            task.refresh_from_db()

        # Search for 'bug'
        results = Task.objects.search_tasks(user, 'bug')
        assert results.count() == 1
        assert results[0].id == task1.id

    def test_search_tasks_with_relevance_ranking(self, user, workspace, task_list):
        """Test that search results are ranked by relevance."""
        # Task with 'urgent' in title (higher weight)
        task1 = Task.objects.create(
            title='urgent priority task',
            description='Some description',
            priority='P1',
            task_list=task_list,
            created_by=user
        )
        # Task with 'urgent' in description (lower weight)
        task2 = Task.objects.create(
            title='Regular task',
            description='This is urgent work',
            priority='P2',
            task_list=task_list,
            created_by=user
        )

        for task in [task1, task2]:
            task.refresh_from_db()

        # Search for 'urgent'
        results = list(Task.objects.search_tasks(user, 'urgent'))

        # Title matches should rank higher than description matches
        assert len(results) == 2
        assert results[0].id == task1.id  # Title match ranks first
        assert results[1].id == task2.id

    def test_search_tasks_permission_filtering(self, user, user2, workspace, workspace2, task_list, task_list2):
        """Test that search respects user permissions."""
        # Task in user's workspace
        task1 = Task.objects.create(
            title='My task with search term',
            priority='P1',
            task_list=task_list,
            created_by=user
        )
        # Task in another user's workspace
        task2 = Task.objects.create(
            title='Other task with search term',
            priority='P1',
            task_list=task_list2,
            created_by=user2
        )

        for task in [task1, task2]:
            task.refresh_from_db()

        # User should only see their own task
        results = Task.objects.search_tasks(user, 'search')
        assert results.count() == 1
        assert results[0].id == task1.id

    def test_search_with_status_filter(self, user, workspace, task_list):
        """Test filtering search results by status."""
        # Active task
        task1 = Task.objects.create(
            title='Active searchable task',
            priority='P1',
            status='active',
            task_list=task_list,
            created_by=user
        )
        # Completed task
        task2 = Task.objects.create(
            title='Completed searchable task',
            priority='P2',
            status='completed',
            task_list=task_list,
            created_by=user
        )

        for task in [task1, task2]:
            task.refresh_from_db()

        # Search with active filter
        results = Task.objects.search_tasks(user, 'searchable', filters={'status': 'active'})
        assert results.count() == 1
        assert results[0].id == task1.id

        # Search with completed filter
        results = Task.objects.search_tasks(user, 'searchable', filters={'status': 'completed'})
        assert results.count() == 1
        assert results[0].id == task2.id

    def test_search_with_priority_filter(self, user, workspace, task_list):
        """Test filtering search results by priority."""
        task1 = Task.objects.create(
            title='High priority searchable',
            priority='P1',
            task_list=task_list,
            created_by=user
        )
        task2 = Task.objects.create(
            title='Low priority searchable',
            priority='P4',
            task_list=task_list,
            created_by=user
        )

        for task in [task1, task2]:
            task.refresh_from_db()

        # Filter by P1 priority only
        results = Task.objects.search_tasks(user, 'searchable', filters={'priority': ['P1']})
        assert results.count() == 1
        assert results[0].id == task1.id

    def test_search_with_tag_filter(self, user, workspace, task_list):
        """Test filtering search results by tags."""
        # Create tags
        tag1 = Tag.objects.create(
            name='backend',
            workspace=workspace,
            created_by=user
        )
        tag2 = Tag.objects.create(
            name='frontend',
            workspace=workspace,
            created_by=user
        )

        # Create tasks with tags
        task1 = Task.objects.create(
            title='Backend searchable task',
            priority='P1',
            task_list=task_list,
            created_by=user
        )
        task1.tags.add(tag1)

        task2 = Task.objects.create(
            title='Frontend searchable task',
            priority='P2',
            task_list=task_list,
            created_by=user
        )
        task2.tags.add(tag2)

        for task in [task1, task2]:
            task.refresh_from_db()

        # Filter by backend tag
        results = Task.objects.search_tasks(user, 'searchable', filters={'tag_names': ['backend']})
        assert results.count() == 1
        assert results[0].id == task1.id

    def test_apply_search_sort_relevance(self, user, workspace, task_list):
        """Test sorting search results by relevance."""
        task1 = Task.objects.create(
            title='task alpha',
            priority='P1',
            task_list=task_list,
            created_by=user
        )
        task2 = Task.objects.create(
            title='task beta',
            priority='P2',
            task_list=task_list,
            created_by=user
        )

        for task in [task1, task2]:
            task.refresh_from_db()

        # Get search results
        results = Task.objects.search_tasks(user, 'task')

        # Apply sort by relevance (default)
        sorted_results = Task.objects.apply_search_sort(results, 'relevance')
        assert list(sorted_results) == list(results)  # Should maintain relevance order

    def test_search_excludes_archived_tasks(self, user, workspace, task_list):
        """Test that archived tasks are excluded from search results."""
        task1 = Task.objects.create(
            title='Active searchable task',
            priority='P1',
            task_list=task_list,
            created_by=user,
            is_archived=False
        )
        task2 = Task.objects.create(
            title='Archived searchable task',
            priority='P2',
            task_list=task_list,
            created_by=user,
            is_archived=True
        )

        for task in [task1, task2]:
            task.refresh_from_db()

        # Only non-archived task should appear
        results = Task.objects.search_tasks(user, 'searchable')
        assert results.count() == 1
        assert results[0].id == task1.id
