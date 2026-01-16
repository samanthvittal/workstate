"""
Celery configuration for Workstate project.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workstate.settings')

app = Celery('workstate')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'sync-active-timers-every-60-seconds': {
        'task': 'time_tracking.sync_active_timers',
        'schedule': 60.0,  # Run every 60 seconds
    },
}

app.conf.timezone = 'UTC'


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')
