"""
Views for user registration and email verification.
"""
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress, EmailConfirmation
from allauth.account.adapter import get_adapter

from .forms import RegistrationForm
from .models import Workspace


@require_http_methods(["GET", "POST"])
def register_view(request):
    """
    User registration view with email/password.
    Creates user account and sends email verification.

    On successful registration:
    - Creates User account (inactive until email verification)
    - UserProfile, UserPreference, and Workspace are created via signals
    - Sends email verification email via django-allauth
    - Redirects to email verification sent page

    For duplicate emails:
    - Redirects to login page with email prepopulated
    - Displays message suggesting login or password reset
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            # Get cleaned data
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            full_name = form.cleaned_data['full_name']
            workspace_name = form.cleaned_data.get('workspace_name', '').strip()
            job_title = form.cleaned_data.get('job_title', '')
            company = form.cleaned_data.get('company', '')
            phone_number = form.cleaned_data.get('phone_number', '')

            # Create user account
            # In dev mode (optional verification), user is active immediately
            # In prod mode (mandatory verification), user is inactive until verified
            from django.conf import settings
            is_active = (settings.ACCOUNT_EMAIL_VERIFICATION != 'mandatory')

            user = User.objects.create_user(
                username=email,  # Use email as username
                email=email,
                password=password,
                is_active=is_active
            )

            # Update user profile with provided information
            # Profile is created by signal, so we fetch and update it
            profile = user.profile
            profile.full_name = full_name
            profile.job_title = job_title
            profile.company = company
            profile.phone_number = phone_number
            profile.save()

            # Update workspace name if provided
            if workspace_name:
                # Find the personal workspace created by signal
                workspace = Workspace.objects.filter(
                    owner=user,
                    is_personal=True
                ).first()
                if workspace:
                    workspace.name = workspace_name
                    workspace.save()

            # Create EmailAddress record for django-allauth
            email_address = EmailAddress.objects.create(
                user=user,
                email=email,
                primary=True,
                verified=False
            )

            # Create EmailConfirmation and send verification email
            email_confirmation = EmailConfirmation.create(email_address)
            email_confirmation.send(request, signup=True)

            # Add success message
            messages.success(
                request,
                'Registration successful! Please check your email to verify your account.'
            )

            # Redirect to email verification sent page
            return redirect('account_email_verification_sent')

        else:
            # Check if error is due to duplicate email
            if 'email' in form.errors:
                email = request.POST.get('email', '')
                messages.warning(
                    request,
                    'An account with this email already exists. Please log in or reset your password if you forgot it.'
                )
                # Redirect to login with email prepopulated
                return redirect(f"{reverse_lazy('accounts:login')}?email={email}")

    else:
        form = RegistrationForm()

    context = {
        'form': form,
    }

    return render(request, 'accounts/register.html', context)
