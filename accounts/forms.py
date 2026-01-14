"""
Forms for user authentication and password reset.
"""
from django import forms
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
import pytz

from accounts.models import UserProfile, UserPreference, LoginAttempt


class RegistrationForm(forms.Form):
    """
    User registration form with required and optional fields.
    """
    # Required fields
    email = forms.EmailField(
        label="Email address",
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'your@email.com',
            'autocomplete': 'email',
        })
    )
    password1 = forms.CharField(
        label="Password",
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter password (min 8 characters)',
            'autocomplete': 'new-password',
            'x-model': 'password',
        }),
        help_text="Your password must be at least 8 characters long.",
    )
    password2 = forms.CharField(
        label="Confirm password",
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password',
        }),
    )
    full_name = forms.CharField(
        label="Full name",
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'John Doe',
            'autocomplete': 'name',
        })
    )

    # Optional fields
    workspace_name = forms.CharField(
        label="Workspace name (optional)",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'My Workspace',
        }),
        help_text="Leave blank to auto-generate a workspace name.",
    )
    job_title = forms.CharField(
        label="Job title (optional)",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Software Developer',
        })
    )
    company = forms.CharField(
        label="Company (optional)",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Acme Corporation',
        })
    )
    phone_number = forms.CharField(
        label="Phone number (optional)",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '+1 (555) 123-4567',
            'autocomplete': 'tel',
        })
    )

    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists. Please log in instead."
            )
        return email

    def clean_password1(self):
        """Validate password strength."""
        password = self.cleaned_data.get('password1')
        if password:
            validate_password(password)
        return password

    def clean(self):
        """Validate that passwords match."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields must match.")

        return cleaned_data


class LoginForm(forms.Form):
    """
    Login form with email and password fields.
    Includes account lockout checking and "Remember Me" functionality.
    """
    email = forms.EmailField(
        label="Email address",
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'your@email.com',
            'autocomplete': 'email',
        }),
        error_messages={
            'required': 'Please enter your email address.',
            'invalid': 'Please enter a valid email address.',
        }
    )

    password = forms.CharField(
        label="Password",
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
            'x-model': 'password',
        }),
        error_messages={
            'required': 'Please enter your password.',
        }
    )

    remember_me = forms.BooleanField(
        label="Remember me for 30 days",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
        })
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.user_cache = None

    def clean(self):
        """
        Validate login credentials and check account lockout status.
        """
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            # Check if user exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise forms.ValidationError(
                    'Invalid email or password. Please try again.',
                    code='invalid_login'
                )

            # Check if account is locked
            if LoginAttempt.is_account_locked(user):
                lockout_end = LoginAttempt.get_lockout_end_time(user)
                if lockout_end:
                    time_remaining = lockout_end - timezone.now()
                    minutes_remaining = max(1, int(time_remaining.total_seconds() / 60))
                    raise forms.ValidationError(
                        f'Your account has been locked due to multiple failed login attempts. '
                        f'Please try again in approximately {minutes_remaining} minutes.',
                        code='account_locked'
                    )

            # Authenticate user
            self.user_cache = authenticate(
                self.request,
                username=email,
                password=password
            )

            if self.user_cache is None:
                # Record failed login attempt
                ip_address = self.get_client_ip()
                LoginAttempt.objects.create(
                    user=user,
                    is_successful=False,
                    ip_address=ip_address
                )

                # Check if account is now locked after this failed attempt
                if LoginAttempt.is_account_locked(user):
                    raise forms.ValidationError(
                        'Your account has been locked due to multiple failed login attempts. '
                        'Please try again in 30 minutes.',
                        code='account_locked'
                    )

                raise forms.ValidationError(
                    'Invalid email or password. Please try again.',
                    code='invalid_login'
                )

            # Check if account is active
            if not self.user_cache.is_active:
                raise forms.ValidationError(
                    'This account is inactive. Please contact support.',
                    code='inactive_account'
                )

        return cleaned_data

    def get_client_ip(self):
        """Get the client's IP address from the request"""
        if self.request:
            x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = self.request.META.get('REMOTE_ADDR')
            return ip
        return None

    def get_user(self):
        """Return the authenticated user"""
        return self.user_cache


class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form with single email field.
    Uses Django's built-in password reset functionality.
    """
    email = forms.EmailField(
        label="Email address",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
        })
    )

    def get_users(self, email):
        """
        Return users with matching email.
        Override to ensure we only get active users.
        """
        active_users = User.objects.filter(
            email__iexact=email,
            is_active=True,
        )
        return (
            u for u in active_users
            if u.has_usable_password()
        )


class CustomSetPasswordForm(SetPasswordForm):
    """
    Custom set password form for password reset confirmation.
    Applies password validation (minimum 8 characters).
    """
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password',
            'x-model': 'password',
        }),
        strip=False,
        help_text="Your password must be at least 8 characters long.",
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password',
        }),
        strip=False,
    )


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile information.
    Email field is read-only and displayed for reference only.
    """
    email = forms.EmailField(
        required=False,
        disabled=True,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 bg-gray-50 cursor-not-allowed',
            'readonly': 'readonly'
        }),
        help_text="Email address cannot be changed after verification"
    )

    full_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'Enter your full name'
        })
    )

    job_title = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'e.g., Senior Developer'
        })
    )

    company = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'Company name'
        })
    )

    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': '+1234567890',
            'type': 'tel'
        })
    )

    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
            'accept': 'image/jpeg,image/jpg,image/png,image/gif',
            'x-on:change': 'previewAvatar($event)'
        }),
        help_text="Upload a profile picture (JPG, PNG, or GIF, max 5MB)"
    )

    class Meta:
        model = UserProfile
        fields = ['full_name', 'avatar', 'job_title', 'company', 'phone_number']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Set email field value from user
        if self.user:
            self.fields['email'].initial = self.user.email

    def clean_avatar(self):
        """Validate avatar file type and size."""
        avatar = self.cleaned_data.get('avatar')

        if avatar:
            # Check file size (5MB max)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if avatar.size > max_size:
                raise ValidationError(
                    f"Avatar file size must be no more than 5MB. Current size: {avatar.size / (1024 * 1024):.2f}MB"
                )

            # Check file extension
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
            file_extension = avatar.name.split('.')[-1].lower()

            if file_extension not in allowed_extensions:
                raise ValidationError(
                    f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
                )

        return avatar


class PreferencesUpdateForm(forms.ModelForm):
    """
    Form for updating user preferences including timezone, date/time formats, and week start day.
    Timezone can be auto-detected from browser using Alpine.js.
    """
    timezone = forms.ChoiceField(
        choices=[(tz, tz) for tz in pytz.common_timezones],
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'x-model': 'selectedTimezone'
        }),
        help_text="Your timezone is auto-detected, but you can change it manually"
    )

    date_format = forms.ChoiceField(
        choices=UserPreference.DATE_FORMAT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        }),
        help_text="Choose how dates should be displayed throughout the application"
    )

    time_format = forms.ChoiceField(
        choices=UserPreference.TIME_FORMAT_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'mr-2'
        }),
        help_text="Choose between 12-hour (e.g., 2:30 PM) or 24-hour (e.g., 14:30) format"
    )

    week_start_day = forms.ChoiceField(
        choices=UserPreference.WEEK_START_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'mr-2'
        }),
        help_text="Choose which day your week starts on for calendar views"
    )

    class Meta:
        model = UserPreference
        fields = ['timezone', 'date_format', 'time_format', 'week_start_day']

    def clean_timezone(self):
        """Validate timezone is a valid pytz timezone."""
        timezone_str = self.cleaned_data.get('timezone')

        if timezone_str and timezone_str not in pytz.common_timezones:
            raise ValidationError("Please select a valid timezone from the list")

        return timezone_str
