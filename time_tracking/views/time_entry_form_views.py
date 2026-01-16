"""
Time entry form views for create and edit operations.

Provides HTML form views with intelligent mode switching and inline editing.
"""
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib import messages

from accounts.mixins import WorkspaceContextMixin
from time_tracking.models import TimeEntry
from time_tracking.forms import TimeEntryForm

logger = logging.getLogger(__name__)


class TimeEntryCreateFormView(LoginRequiredMixin, WorkspaceContextMixin, View):
    """
    Time entry create form view.

    GET /time/entries/new/
    POST /time/entries/new/

    Displays form with three input modes and handles creation.
    """

    def get(self, request):
        """Handle GET request for time entry create form."""
        # Get workspace context from mixin
        workspace_context = self.get_workspace_context(request)

        form = TimeEntryForm(user=request.user)

        context = {
            **workspace_context,  # Spread workspace context from mixin
            'form': form,
            'time_entry': None,
        }

        return render(request, 'time_tracking/time_entry_form.html', context)

    def post(self, request):
        """Handle POST request to create time entry."""
        # Get workspace context from mixin
        workspace_context = self.get_workspace_context(request)

        form = TimeEntryForm(data=request.POST, user=request.user)

        if form.is_valid():
            try:
                time_entry = form.save()
                messages.success(request, 'Time entry created successfully.')
                return redirect('time_tracking:time-entry-list-html')
            except Exception as e:
                logger.error(f"Error creating time entry: {e}", exc_info=True)
                messages.error(request, 'An error occurred while creating the time entry. Please try again.')

        context = {
            **workspace_context,  # Spread workspace context from mixin
            'form': form,
            'time_entry': None,
        }

        return render(request, 'time_tracking/time_entry_form.html', context)


class TimeEntryEditFormView(LoginRequiredMixin, WorkspaceContextMixin, View):
    """
    Time entry edit form view.

    GET /time/entries/<id>/edit/
    POST /time/entries/<id>/edit/

    Displays pre-filled form and handles updates.
    """

    def get(self, request, entry_id):
        """Handle GET request for time entry edit form."""
        time_entry = get_object_or_404(
            TimeEntry,
            id=entry_id,
            user=request.user
        )

        # Prevent editing running timers (must use timer API)
        if time_entry.is_running:
            messages.error(request, 'Cannot edit a running timer. Please stop the timer first.')
            return redirect('time_tracking:time-entry-list-html')

        # Get workspace context from mixin
        workspace_context = self.get_workspace_context(request)

        form = TimeEntryForm(instance=time_entry, user=request.user)

        context = {
            **workspace_context,  # Spread workspace context from mixin
            'form': form,
            'time_entry': time_entry,
        }

        # Check if request is AJAX (for inline edit modal)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'time_tracking/components/time_entry_edit_form_partial.html', context)

        return render(request, 'time_tracking/time_entry_form.html', context)

    def post(self, request, entry_id):
        """Handle POST request to update time entry."""
        time_entry = get_object_or_404(
            TimeEntry,
            id=entry_id,
            user=request.user
        )

        # Prevent editing running timers
        if time_entry.is_running:
            messages.error(request, 'Cannot edit a running timer. Please stop the timer first.')
            return redirect('time_tracking:time-entry-list-html')

        # Get workspace context from mixin
        workspace_context = self.get_workspace_context(request)

        form = TimeEntryForm(data=request.POST, instance=time_entry, user=request.user)

        if form.is_valid():
            try:
                time_entry = form.save()
                messages.success(request, 'Time entry updated successfully.')

                # Check if request is AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    # Return updated row HTML for HTMX swap
                    context = {'entry': time_entry}
                    return render(request, 'time_tracking/components/time_entry_row.html', context)

                return redirect('time_tracking:time-entry-list-html')
            except Exception as e:
                logger.error(f"Error updating time entry: {e}", exc_info=True)
                messages.error(request, 'An error occurred while updating the time entry. Please try again.')

        context = {
            **workspace_context,  # Spread workspace context from mixin
            'form': form,
            'time_entry': time_entry,
        }

        # Check if request is AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'time_tracking/components/time_entry_edit_form_partial.html', context)

        return render(request, 'time_tracking/time_entry_form.html', context)


class TimeEntryInlineEditView(LoginRequiredMixin, View):
    """
    Time entry inline edit view for HTMX partial updates.

    GET /time/entries/<id>/inline-edit/

    Returns inline edit form for modal display.
    """

    def get(self, request, entry_id):
        """Handle GET request for inline edit form."""
        time_entry = get_object_or_404(
            TimeEntry,
            id=entry_id,
            user=request.user
        )

        # Prevent editing running timers
        if time_entry.is_running:
            context = {
                'error_message': 'Cannot edit a running timer. Please stop the timer first.'
            }
            return render(request, 'time_tracking/components/time_entry_edit_error.html', context)

        form = TimeEntryForm(instance=time_entry, user=request.user)

        context = {
            'form': form,
            'time_entry': time_entry,
        }

        return render(request, 'time_tracking/components/time_entry_inline_edit_form.html', context)
