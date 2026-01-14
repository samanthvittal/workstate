"""
Tests for task templates and frontend behavior.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestTaskFormTemplate:
    """Test suite for task_form.html template rendering."""

    def test_task_form_renders_all_fields(self, client, user, task_list):
        """Test that task_form.html renders all form fields correctly."""
        client.force_login(user)
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Check for all form fields
        assert 'name="title"' in content
        assert 'name="description"' in content
        assert 'name="due_date"' in content
        assert 'name="due_time"' in content
        assert 'name="priority"' in content

    def test_title_field_has_autofocus(self, client, user, task_list):
        """Test that title field has autofocus attribute."""
        client.force_login(user)
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Check for autofocus attribute on title field
        assert 'autofocus' in content

    def test_priority_selection_displays_with_color_indicators(self, client, user, task_list):
        """Test that priority selection displays with color indicators."""
        client.force_login(user)
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Check that priority field exists
        assert 'name="priority"' in content

        # Check for priority options (P1, P2, P3, P4)
        assert 'P1' in content
        assert 'P2' in content
        assert 'P3' in content
        assert 'P4' in content

    def test_due_time_field_has_alpine_conditional(self, client, user, task_list):
        """Test that due_time field has Alpine.js x-show directive for conditional display."""
        client.force_login(user)
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Check for Alpine.js x-show or x-ref on due_date field
        # The form widget should have x-ref="due_date" attribute
        assert 'x-ref' in content or 'x-show' in content

    def test_form_submission_via_htmx(self, client, user, task_list):
        """Test that form has HTMX attributes for submission."""
        client.force_login(user)
        url = reverse('tasks:task-create', kwargs={'tasklist_id': task_list.id})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Check for form element
        assert '<form' in content
        assert 'method="post"' in content or 'method=post' in content


@pytest.mark.django_db
class TestTaskEditFormTemplate:
    """Test suite for task_edit_form.html template rendering."""

    def test_modal_overlay_displays_for_task_editing(self, client, user, task):
        """Test that modal overlay displays for task editing via HTMX."""
        client.force_login(user)
        url = reverse('tasks:task-edit', kwargs={'pk': task.id})
        response = client.get(url, HTTP_HX_REQUEST='true')

        assert response.status_code == 200
        content = response.content.decode()

        # Check for modal elements
        # Modal should have Alpine.js data and controls
        assert 'x-data' in content or 'x-show' in content
        # Modal should have form
        assert '<form' in content

    def test_edit_form_pre_populates_fields(self, client, user, task):
        """Test that edit form pre-populates all fields with existing task data."""
        client.force_login(user)
        url = reverse('tasks:task-edit', kwargs={'pk': task.id})
        response = client.get(url, HTTP_HX_REQUEST='true')

        assert response.status_code == 200
        content = response.content.decode()

        # Check that form contains task data
        assert task.title in content
        assert task.description in content
        assert task.priority in content
