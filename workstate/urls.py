"""
URL configuration for workstate project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.dashboard_views import dashboard_view
from accounts.home_views import home_view

urlpatterns = [
    # Home page - redirects based on authentication status
    path('', home_view, name='home'),

    # Dashboard
    path('dashboard/', dashboard_view, name='dashboard'),

    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('', include('tasks.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
