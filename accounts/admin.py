"""
Django admin configuration for accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    """Extended User admin with profile inline."""
    inlines = (UserProfileInline,)
    list_display = ('email', 'get_full_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'profile__full_name')
    ordering = ('-date_joined',)

    def get_full_name(self, obj):
        """Get full name from profile."""
        return obj.profile.full_name if hasattr(obj, 'profile') else ''
    get_full_name.short_description = 'Full Name'


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""
    list_display = ('user', 'full_name', 'timezone', 'created_at')
    list_filter = ('timezone', 'created_at')
    search_fields = ('full_name', 'user__email', 'company', 'job_title')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name', 'avatar')
        }),
        ('Professional Details', {
            'fields': ('job_title', 'company', 'phone_number')
        }),
        ('Preferences', {
            'fields': ('timezone',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
