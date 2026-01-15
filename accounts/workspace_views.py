"""
Workspace management views.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Workspace


@login_required
def workspace_create_view(request):
    """
    Create new workspace with modal form or redirect.
    Validates workspace name and checks for duplicates.
    """
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        # Validate name
        if not name:
            messages.error(request, 'Workspace name is required.')
            return render(request, 'accounts/workspace_create_form.html')

        # Check for duplicate workspace name
        if Workspace.objects.filter(owner=request.user, name=name).exists():
            messages.error(request, f'You already have a workspace named "{name}".')
            return render(request, 'accounts/workspace_create_form.html')

        # Create workspace
        workspace = Workspace.objects.create(
            name=name,
            owner=request.user,
            is_personal=False
        )

        messages.success(request, f'Workspace "{workspace.name}" created!')
        return redirect(f'/dashboard/?workspace={workspace.id}')

    return render(request, 'accounts/workspace_create_form.html')
