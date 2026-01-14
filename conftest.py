"""
Shared pytest configuration and fixtures.
"""
import pytest
import django
from django.conf import settings

# Configure Django settings before importing Django components
django.setup()


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
