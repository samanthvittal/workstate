"""
Views for user time tracking settings and preferences.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.contrib import messages

from accounts.mixins import WorkspaceContextMixin
from time_tracking.forms import UserTimePreferencesForm
from time_tracking.models import UserTimePreferences


class TimeTrackingSettingsView(LoginRequiredMixin, WorkspaceContextMixin, FormView):
    """
    View for displaying and updating user time tracking preferences.

    Provides form for editing time rounding, idle detection, Pomodoro timer,
    and billable rate settings.
    """

    template_name = 'time_tracking/settings.html'
    form_class = UserTimePreferencesForm
    success_url = reverse_lazy('time_tracking:settings')

    def get_form_kwargs(self):
        """Add user and instance to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user

        # Get or create preferences instance for this user
        try:
            instance = UserTimePreferences.objects.get(user=self.request.user)
            kwargs['instance'] = instance
        except UserTimePreferences.DoesNotExist:
            # No instance yet, form will create one on save
            pass

        return kwargs

    def form_valid(self, form):
        """Save preferences and show success message."""
        form.save()
        messages.success(
            self.request,
            'Your time tracking preferences have been saved successfully.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """Show error message on validation failure."""
        messages.error(
            self.request,
            'There was an error saving your preferences. Please check the form and try again.'
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Add additional context for template."""
        # WorkspaceContextMixin automatically adds workspace context via super()
        context = super().get_context_data(**kwargs)

        context['page_title'] = 'Time Tracking Settings'
        context['page_description'] = 'Configure your time tracking preferences, including time rounding, idle detection, Pomodoro timer, and billable rates.'

        # Add rounding examples for help text
        context['rounding_examples'] = {
            5: {
                'up': '1h 3m → 1h 5m',
                'down': '1h 3m → 1h 0m',
                'nearest': '1h 3m → 1h 5m, 1h 2m → 1h 0m',
            },
            15: {
                'up': '1h 10m → 1h 15m',
                'down': '1h 10m → 1h 0m',
                'nearest': '1h 10m → 1h 15m, 1h 5m → 1h 0m',
            },
        }

        return context
