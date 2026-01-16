"""
Shared pytest configuration and fixtures.
"""
import pytest
from django.conf import settings

# Configure test cache before Django setup
def pytest_configure(config):
    """Configure test settings."""
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-cache',
        }
    }


@pytest.fixture(scope='session')
def django_db_setup():
    """
    Configure test database setup.
    """
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'ATOMIC_REQUESTS': True,
    }
