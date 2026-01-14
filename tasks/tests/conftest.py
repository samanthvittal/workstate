"""
Shared pytest fixtures for task tests.
"""
import pytest
from django.contrib.auth.models import User
from accounts.models import Workspace
from tasks.models import Task, TaskList


@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def user2():
    """Create a second test user for isolation testing."""
    return User.objects.create_user(
        username='testuser2',
        email='test2@example.com',
        password='testpass456'
    )


@pytest.fixture
def workspace(user):
    """Create a test workspace."""
    return Workspace.objects.create(
        name='Test Workspace',
        owner=user
    )


@pytest.fixture
def workspace2(user2):
    """Create a second test workspace for isolation testing."""
    return Workspace.objects.create(
        name='Test Workspace 2',
        owner=user2
    )


@pytest.fixture
def task_list(user, workspace):
    """Create a test task list."""
    return TaskList.objects.create(
        name='Test Task List',
        description='Test task list description',
        workspace=workspace,
        created_by=user
    )


@pytest.fixture
def task_list2(user2, workspace2):
    """Create a second test task list for isolation testing."""
    return TaskList.objects.create(
        name='Test Task List 2',
        workspace=workspace2,
        created_by=user2
    )


@pytest.fixture
def task(user, task_list):
    """Create a test task."""
    return Task.objects.create(
        title='Test Task',
        description='Test task description',
        priority='P2',
        task_list=task_list,
        created_by=user
    )
