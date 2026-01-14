#!/usr/bin/env python
"""
Manual verification script for Task Group 4.
Verifies URL configuration and basic integration functionality.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workstate.settings')
django.setup()

from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import Workspace
from tasks.models import Task


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)


def verify_url_configuration():
    """Verify URL configuration and namespacing."""
    print_section("Task 4.2 & 4.3: URL Configuration Verification")

    # Check if users and workspaces exist
    user_count = User.objects.count()
    workspace_count = Workspace.objects.count()

    print(f"Users in database: {user_count}")
    print(f"Workspaces in database: {workspace_count}")

    if user_count == 0:
        print("\nNo users found. Creating test user...")
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        print(f"Created user: {user.username}")
    else:
        user = User.objects.first()
        print(f"Using existing user: {user.username}")

    if workspace_count == 0:
        print("\nNo workspaces found. Creating test workspace...")
        workspace = Workspace.objects.create(
            name='Test Workspace',
            owner=user
        )
        print(f"Created workspace: {workspace.name}")
    else:
        workspace = Workspace.objects.first()
        print(f"Using existing workspace: {workspace.name}")

    # Test URL reverse resolution
    print("\nTesting URL reverse resolution:")

    try:
        create_url = reverse('tasks:task-create', kwargs={'workspace_id': workspace.id})
        print(f"✓ Task create URL: {create_url}")
    except Exception as e:
        print(f"✗ Task create URL failed: {e}")

    # Create a test task to verify edit URL
    task = Task.objects.filter(workspace=workspace).first()
    if not task:
        task = Task.objects.create(
            title='Test Task for URL Verification',
            priority='P1',
            workspace=workspace,
            created_by=user
        )
        print(f"Created test task: {task.title}")

    try:
        edit_url = reverse('tasks:task-edit', kwargs={'pk': task.id})
        print(f"✓ Task edit URL: {edit_url}")
    except Exception as e:
        print(f"✗ Task edit URL failed: {e}")


def verify_modal_container():
    """Verify modal container in base template."""
    print_section("Task 4.4: Modal Container Verification")

    base_template_path = 'templates/base.html'
    if os.path.exists(base_template_path):
        with open(base_template_path, 'r') as f:
            content = f.read()
            if '<div id="modal"' in content:
                print("✓ Modal container found in base.html")
                if 'z-50' in content or 'z-index: 50' in content:
                    print("✓ Modal container has proper z-index for overlay stacking")
                else:
                    print("⚠ Modal container might need z-index for proper stacking")
            else:
                print("✗ Modal container not found in base.html")
    else:
        print(f"✗ Base template not found at {base_template_path}")


def verify_test_counts():
    """Verify test counts meet requirements."""
    print_section("Task 4.5 & 4.6: Test Verification")

    import subprocess

    print("Running pytest to count tests...")
    result = subprocess.run(
        ['python', '-m', 'pytest', 'tasks/tests/', '--collect-only', '-q'],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'test' in line.lower():
                print(line)

        # Count tests
        test_count = result.stdout.count('test_')
        print(f"\n✓ Total tests found: {test_count}")

        if 16 <= test_count <= 34:
            print(f"✓ Test count is within expected range (16-34 tests)")
        else:
            print(f"⚠ Test count is outside expected range (found {test_count}, expected 16-34)")
    else:
        print(f"✗ Could not collect tests: {result.stderr}")


def verify_task_operations():
    """Verify basic task operations work."""
    print_section("Integration Verification: Task Operations")

    user = User.objects.first()
    workspace = Workspace.objects.filter(owner=user).first()

    if not user or not workspace:
        print("✗ Cannot verify task operations without user and workspace")
        return

    # Create a task
    print("\n1. Testing task creation...")
    task = Task.objects.create(
        title='Integration Verification Task',
        description='This task verifies the integration is working',
        priority='P2',
        workspace=workspace,
        created_by=user
    )
    print(f"✓ Task created: {task.title} (ID: {task.id})")

    # Update the task
    print("\n2. Testing task update...")
    task.title = 'Updated Integration Task'
    task.priority = 'P1'
    task.status = 'completed'
    task.save()
    print(f"✓ Task updated: {task.title} (Priority: {task.priority}, Status: {task.status})")

    # Query tasks
    print("\n3. Testing task queries...")
    tasks = Task.objects.filter(workspace=workspace)
    print(f"✓ Found {tasks.count()} tasks in workspace '{workspace.name}'")

    # Cleanup
    print("\n4. Cleaning up verification task...")
    task.delete()
    print("✓ Verification task deleted")


def print_manual_checklist():
    """Print manual verification checklist."""
    print_section("Task 4.7: Manual Verification Checklist")

    workspace = Workspace.objects.first()

    checklist = [
        f"[ ] Visit http://localhost:8000/workspace/{workspace.id if workspace else '1'}/tasks/create/ and verify form loads",
        "[ ] Submit valid task and verify success message",
        "[ ] Verify form resets after creation",
        "[ ] Create a second task quickly to test workflow",
        "[ ] Click edit on a task and verify modal loads via HTMX",
        "[ ] Update task in modal and verify changes save",
        "[ ] Test mobile responsive design (resize browser)",
        "[ ] Test priority color indicators display correctly",
        "[ ] Test due time field shows/hides based on due date",
    ]

    print("\nManual verification steps to perform in browser:")
    print("\n1. Start the development server:")
    print("   python manage.py runserver")
    print("\n2. Complete the following checklist:\n")
    for item in checklist:
        print(f"   {item}")

    print("\nNote: Make sure you have created a user account and workspace first.")
    print("You can create these through the Django admin or registration flow.")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Task Group 4: URL Configuration & Full Integration Testing")
    print("Verification Script")
    print("="*60)

    verify_url_configuration()
    verify_modal_container()
    verify_test_counts()
    verify_task_operations()
    print_manual_checklist()

    print("\n" + "="*60)
    print("Verification Complete")
    print("="*60 + "\n")
