"""
Search views for task search functionality.

Provides views for live search dropdown, full search results page,
saved searches, and search history management.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import ListView

from tasks.models import Task, SavedSearch, SearchHistory
from tasks.services import SearchQueryService


class SearchDropdownView(LoginRequiredMixin, View):
    """
    View for live search preview dropdown in navigation bar.

    Returns partial template with up to 5 preview results.
    Triggered by HTMX with debounced input (300ms delay).
    """

    def get(self, request):
        """Handle GET request for search dropdown preview."""
        query = request.GET.get('q', '').strip()

        if not query:
            # Return empty dropdown when query is cleared
            return render(request, 'search/_search_dropdown.html', {
                'query': '',
                'tasks': [],
                'result_count': 0,
            })

        # Sanitize input
        query = SearchQueryService.sanitize_input(query)

        # Search tasks with limit of 5 for preview
        tasks = Task.objects.search_tasks(
            user=request.user,
            query=query,
            filters=None
        )[:5]

        # Get total count for "View all results" link
        total_count = Task.objects.search_tasks(
            user=request.user,
            query=query,
            filters=None
        ).count()

        return render(request, 'search/_search_dropdown.html', {
            'query': query,
            'tasks': tasks,
            'result_count': total_count,
        })


class SearchResultsView(LoginRequiredMixin, ListView):
    """
    View for full search results page with filtering, sorting, and pagination.

    Displays paginated search results (25 per page) with filters sidebar,
    recent searches, and saved searches.
    """
    model = Task
    template_name = 'search/search_results.html'
    context_object_name = 'tasks'
    paginate_by = 25

    def get_queryset(self):
        """Get search results with filters and sorting applied."""
        query = self.request.GET.get('q', '').strip()

        if not query:
            return Task.objects.none()

        # Sanitize input
        query = SearchQueryService.sanitize_input(query)

        # Build filters dict from query parameters
        filters = {}

        workspace_id = self.request.GET.get('workspace')
        if workspace_id:
            filters['workspace_id'] = workspace_id

        tag_names = self.request.GET.getlist('tags')
        if tag_names:
            filters['tag_names'] = tag_names

        status = self.request.GET.get('status', 'active')
        filters['status'] = status

        priority = self.request.GET.getlist('priority')
        if priority:
            filters['priority'] = priority

        # Get search results with filters
        queryset = Task.objects.search_tasks(
            user=self.request.user,
            query=query,
            filters=filters
        )

        # Apply sorting
        sort_option = self.request.GET.get('sort', 'relevance')
        queryset = Task.objects.apply_search_sort(queryset, sort_option)

        # Store query for recording in get_context_data
        self.search_query = query
        self.result_count = queryset.count()

        return queryset

    def get_context_data(self, **kwargs):
        """Add search metadata, filters, recent searches, and saved searches to context."""
        context = super().get_context_data(**kwargs)

        query = self.request.GET.get('q', '').strip()
        context['query'] = query
        context['result_count'] = getattr(self, 'result_count', 0)

        # Current filters (using template-friendly names)
        context['workspace_filter'] = self.request.GET.get('workspace')
        context['tag_filter'] = self.request.GET.getlist('tags')
        context['status_filter'] = self.request.GET.get('status')  # No default, let template handle it
        context['priority_filters'] = self.request.GET.getlist('priority')
        context['sort'] = self.request.GET.get('sort', 'relevance')

        # Also keep these for backwards compatibility if needed
        context['current_workspace_id'] = context['workspace_filter']
        context['current_tag_names'] = context['tag_filter']
        context['current_status'] = self.request.GET.get('status', 'active')
        context['current_priority'] = context['priority_filters']
        context['current_sort'] = context['sort']

        # Get workspaces for filter dropdown
        from accounts.models import Workspace
        context['workspaces'] = Workspace.objects.filter(owner=self.request.user)
        context['user_workspaces'] = context['workspaces']  # Alias for template compatibility

        # Sort display name for UI
        sort_names = {
            'relevance': 'Relevance',
            'due_date': 'Due Date',
            'priority': 'Priority',
            'created': 'Created Date'
        }
        context['sort_display'] = sort_names.get(context['sort'], 'Relevance')

        # Get all tags used in search results for filter
        from tasks.models import Tag
        context['available_tags'] = Tag.objects.filter(
            tasks__in=context['tasks']
        ).distinct()

        # Recent searches (last 10)
        context['recent_searches'] = SearchHistory.objects.get_recent_for_user(
            user=self.request.user,
            limit=10
        )

        # Saved searches
        context['saved_searches'] = SavedSearch.objects.for_user(self.request.user)

        # Record search in history if query exists and has results
        if query and self.result_count > 0:
            SearchHistory.objects.create(
                user=self.request.user,
                query=query,
                result_count=self.result_count
            )

            # Prune old searches to keep only 50 most recent
            SearchHistory.objects.prune_old_searches(
                user=self.request.user,
                keep_count=50
            )

        return context


class SaveSearchView(LoginRequiredMixin, View):
    """
    View for saving a search query with filters.

    Handles POST request to create a SavedSearch record.
    Validates user has not exceeded 20 saved searches limit.
    """

    def post(self, request):
        """Handle POST request to save search."""
        name = request.POST.get('name', '').strip()
        query = request.POST.get('query', '').strip()

        if not name or not query:
            return JsonResponse({
                'success': False,
                'error': 'Name and query are required.'
            }, status=400)

        # Build filters dict from request
        filters = {}

        workspace_id = request.POST.get('workspace')
        if workspace_id:
            filters['workspace_id'] = workspace_id

        tag_names = request.POST.getlist('tags')
        if tag_names:
            filters['tag_names'] = tag_names

        status = request.POST.get('status')
        if status:
            filters['status'] = status

        priority = request.POST.getlist('priority')
        if priority:
            filters['priority'] = priority

        sort_option = request.POST.get('sort')
        if sort_option:
            filters['sort'] = sort_option

        # Try to create saved search
        try:
            saved_search = SavedSearch.objects.create(
                user=request.user,
                name=name,
                query=query,
                filters=filters
            )

            return JsonResponse({
                'success': True,
                'id': saved_search.id,
                'name': saved_search.name,
                'message': f'Search "{name}" saved successfully!'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class DeleteSearchView(LoginRequiredMixin, View):
    """
    View for deleting a saved search.

    Handles DELETE request to remove a SavedSearch record.
    Verifies saved search belongs to authenticated user.
    """

    def delete(self, request, pk):
        """Handle DELETE request to remove saved search."""
        saved_search = get_object_or_404(SavedSearch, pk=pk)

        # Verify saved search belongs to user
        if saved_search.user != request.user:
            raise PermissionDenied("You do not have permission to delete this search.")

        name = saved_search.name
        saved_search.delete()

        return JsonResponse({
            'success': True,
            'message': f'Search "{name}" deleted successfully.'
        })

    def post(self, request, pk):
        """Handle POST request as DELETE (for browsers that don't support DELETE)."""
        return self.delete(request, pk)


class ClearSearchHistoryView(LoginRequiredMixin, View):
    """
    View for clearing user's search history.

    Handles POST request to delete all SearchHistory records for the user.
    """

    def post(self, request):
        """Handle POST request to clear search history."""
        # Delete all search history for the user
        deleted_count, _ = SearchHistory.objects.filter(user=request.user).delete()

        messages.success(request, f'Search history cleared ({deleted_count} searches removed).')

        # Return the updated recent searches partial (empty state)
        return render(request, 'search/_recent_searches.html', {
            'recent_searches': []
        })
