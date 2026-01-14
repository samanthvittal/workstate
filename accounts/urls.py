"""
URL configuration for accounts app.
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import admin_views
from . import registration_views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('register/', registration_views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Password reset URLs
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Profile and preferences URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_update_view, name='profile_edit'),
    path('preferences/', views.preferences_view, name='preferences'),

    # Admin dashboard URLs
    path('admin-dashboard/', admin_views.admin_user_list, name='admin_user_list'),
    path('admin-dashboard/users/<int:pk>/', admin_views.admin_user_detail, name='admin_user_detail'),

    # Admin action URLs
    path('admin-dashboard/users/<int:user_id>/unlock/', admin_views.admin_unlock_account, name='admin_unlock_account'),
    path('admin-dashboard/users/<int:user_id>/reset-password/', admin_views.admin_trigger_password_reset, name='admin_trigger_password_reset'),
    path('admin-dashboard/users/<int:user_id>/delete/', admin_views.admin_delete_user, name='admin_delete_user'),
    path('admin-dashboard/users/<int:user_id>/toggle-admin/', admin_views.admin_toggle_admin, name='admin_toggle_admin'),
]
