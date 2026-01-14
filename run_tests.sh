#!/bin/bash
# Test runner script for Task Group 1

# Set up environment
export DJANGO_SETTINGS_MODULE=workstate.settings

# Run migrations
echo "Running migrations..."
python3 manage.py migrate --run-syncdb

# Run tests for User and UserProfile models
echo "Running tests for User and UserProfile models..."
python3 -m pytest accounts/tests/test_models.py -v

echo "Tests completed!"
