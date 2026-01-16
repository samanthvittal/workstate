# Idle Time Detection Guide

## Overview

The idle time detection system automatically monitors running timers and notifies users when they've been idle for too long, helping maintain accurate time tracking.

## How It Works

### Detection Process

1. **Celery Background Task:** Every 60 seconds, the `check_idle_timers` task runs
2. **Threshold Check:** Compares elapsed timer time against user's idle threshold
3. **Notification Creation:** If threshold exceeded, creates an idle notification
4. **UI Display:** Frontend polls for notifications every 30 seconds and displays alert

### Default Behavior

- **Default Threshold:** 5 minutes of inactivity
- **Applies To:** Only active (running) timers, not manual entries
- **Frequency:** Checked every minute by Celery task
- **Notification:** Single notification per idle event (no duplicates)

## User Actions

When an idle notification appears, users have three options:

### 1. Keep Time
- **Effect:** No changes to timer
- **Use When:** You were actually working but didn't interact with the system
- **Result:** Timer continues with all time tracked

### 2. Discard Idle Time
- **Effect:** Stops timer and removes all time after idle start
- **Use When:** You stepped away and want to remove the idle period
- **Result:** Timer stopped at idle_start_time, duration adjusted
- **Example:**
  - Timer started: 2:00 PM
  - Idle detected at: 2:05 PM (5-min threshold)
  - Action taken at: 2:15 PM
  - Final duration: 5 minutes (2:00-2:05)

### 3. Stop Timer at Idle Start
- **Effect:** Stops timer at idle start time
- **Use When:** You finished working when idle period began
- **Result:** Timer stopped, time rounding applied if configured
- **Example:**
  - Timer started: 2:00 PM
  - Idle detected at: 2:05 PM
  - Rounding: 15 minutes, round up
  - Final duration: 15 minutes (rounded from 5)

## Configuration

### Setting Idle Threshold

Users can configure their idle threshold in time tracking preferences:

**Default:** 5 minutes

**Options:**
- Any positive integer (minutes)
- Set to 0 to disable idle detection

**Future Enhancement:** UI in user settings page (Task Group 13)

### Current Configuration

The `idle_threshold_minutes` field exists in the `UserTimePreferences` model:

```python
# Default preferences for new users
UserTimePreferences.objects.create(
    user=user,
    idle_threshold_minutes=5  # Default: 5 minutes
)

# Disable idle detection
preferences.idle_threshold_minutes = 0
preferences.save()

# Custom threshold (10 minutes)
preferences.idle_threshold_minutes = 10
preferences.save()
```

## API Endpoints

### Get Pending Notifications
```http
GET /api/timers/idle/notifications/
```

**Response:**
```json
{
  "notifications": [
    {
      "id": 1,
      "time_entry_id": 42,
      "task_name": "Review code",
      "project_name": "Backend API",
      "idle_start_time": "2026-01-16T14:05:00Z",
      "notification_sent_at": "2026-01-16T14:06:00Z",
      "timer_start_time": "2026-01-16T14:00:00Z"
    }
  ],
  "count": 1
}
```

### Keep Time
```http
POST /api/timers/idle/keep/
Content-Type: application/x-www-form-urlencoded

notification_id=1
```

**Response:**
```json
{
  "success": true,
  "message": "Time kept successfully.",
  "notification_id": 1,
  "action": "keep"
}
```

### Discard Idle Time
```http
POST /api/timers/idle/discard/
Content-Type: application/x-www-form-urlencoded

notification_id=1
```

**Response:**
```json
{
  "success": true,
  "message": "Idle time discarded successfully.",
  "notification_id": 1,
  "action": "discard",
  "time_entry_id": 42,
  "new_duration_seconds": 300
}
```

### Stop Timer at Idle Start
```http
POST /api/timers/idle/stop/
Content-Type: application/x-www-form-urlencoded

notification_id=1
```

**Response:**
```json
{
  "success": true,
  "message": "Timer stopped at idle start successfully.",
  "notification_id": 1,
  "action": "stop_at_idle",
  "time_entry_id": 42,
  "duration_seconds": 300
}
```

## Database Schema

### IdleTimeNotification Model

```python
class IdleTimeNotification(models.Model):
    user = models.ForeignKey(User)
    time_entry = models.ForeignKey(TimeEntry)
    idle_start_time = models.DateTimeField()
    notification_sent_at = models.DateTimeField(auto_now_add=True)
    action_taken = models.CharField(
        max_length=20,
        choices=['none', 'keep', 'discard', 'stop_at_idle'],
        default='none'
    )
    action_taken_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Indexes:**
- user_id
- time_entry_id
- action_taken
- (user_id, action_taken) composite

## UI Component

### Location
Fixed position at bottom-right corner of screen

### Display
- Yellow warning theme
- Idle start time and current time
- Task and project information
- Three action buttons
- Helpful explanations
- Dismissible (temporarily)

### Behavior
- Auto-appears when notification detected
- Polls every 30 seconds for new notifications
- Reloads page after action taken
- Shows loading states during API calls

### Integration
Include in base template:
```django
{% include 'time_tracking/components/idle_notification.html' %}
```

## Celery Configuration

### Task Schedule

```python
CELERY_BEAT_SCHEDULE = {
    'check-idle-timers': {
        'task': 'time_tracking.check_idle_timers',
        'schedule': 60.0,  # Every 60 seconds
    },
}
```

### Running Celery

**Start Celery Worker:**
```bash
celery -A workstate worker --loglevel=info
```

**Start Celery Beat (scheduler):**
```bash
celery -A workstate beat --loglevel=info
```

**Combined (for development):**
```bash
celery -A workstate worker --beat --loglevel=info
```

## Testing

### Run Idle Detection Tests
```bash
pytest time_tracking/tests/test_idle_detection.py -v
```

### Manual Testing Workflow

1. **Start a timer:**
   ```http
   POST /api/timers/start/
   task_id=1
   ```

2. **Wait for threshold + 1 minute:**
   - Default: 6 minutes total
   - Or modify start_time in database for faster testing

3. **Celery task runs:**
   - Check logs for "Created idle notification for timer X"

4. **Frontend polls:**
   - Wait up to 30 seconds for notification to appear

5. **Test actions:**
   - Click Keep/Discard/Stop button
   - Verify timer state updated correctly

### Fast Testing (Database Manipulation)

```python
from time_tracking.models import TimeEntry
from django.utils import timezone
from datetime import timedelta

# Create timer with start_time 10 minutes ago
timer = TimeEntry.objects.get(id=1)
timer.start_time = timezone.now() - timedelta(minutes=10)
timer.save()

# Manually trigger idle check
from time_tracking.tasks import check_idle_timers
result = check_idle_timers()
print(result)  # Should show notification created
```

## Logging

All idle detection events are logged:

```python
# Notification created
logger.info(f"Created idle notification for timer {timer.id} (user: {user.email})")

# Action taken
logger.info(f"User {user.email} kept idle time for timer {timer.id}")
logger.info(f"User {user.email} discarded idle time for timer {timer.id}")
logger.info(f"User {user.email} stopped timer {timer.id} at idle start")

# Errors
logger.error(f"Error processing timer {timer.id}: {error}")
logger.error(f"Error during idle detection: {error}")
```

**View logs:**
```bash
# Follow Celery worker logs
tail -f celery.log

# Django logs (if configured)
tail -f django.log
```

## Troubleshooting

### Notifications Not Appearing

1. **Check Celery Beat is running:**
   ```bash
   ps aux | grep celery
   ```

2. **Check task execution:**
   - Look for "Idle detection complete" in logs
   - Verify `notifications_created` count

3. **Check frontend polling:**
   - Open browser console
   - Look for fetch requests to `/api/timers/idle/notifications/`

4. **Check user preferences:**
   ```python
   preferences = UserTimePreferences.objects.get(user=user)
   print(preferences.idle_threshold_minutes)  # Should be > 0
   ```

### Duplicate Notifications

This should not happen due to duplicate prevention logic. If it does:

1. **Check database:**
   ```sql
   SELECT * FROM idle_time_notifications
   WHERE time_entry_id = X AND action_taken = 'none';
   ```

2. **Verify task logic:**
   - Should filter for `action_taken='none'` before creating

### Actions Not Working

1. **Check CSRF token:**
   - Verify cookie exists: `document.cookie`
   - Ensure token passed in headers

2. **Check permissions:**
   - User must own the notification
   - Notification must be pending (`action_taken='none'`)

3. **Check timer state:**
   - Timer must still be running for discard/stop actions

## Best Practices

1. **Don't dismiss notifications repeatedly:**
   - Take action or adjust idle threshold
   - Dismissing only hides temporarily

2. **Configure appropriate threshold:**
   - Too short: Frequent interruptions
   - Too long: Inaccurate time tracking
   - Recommended: 5-15 minutes

3. **Review idle notifications regularly:**
   - Helps identify workflow patterns
   - Adjust threshold based on work style

4. **Use appropriate action:**
   - Keep: For brief distractions (email, Slack)
   - Discard: For extended breaks
   - Stop: When you're actually done working

## Future Enhancements

Potential improvements for later task groups:

1. **WebSocket notifications:** Real-time alerts (Task Group 11)
2. **Sound/browser notifications:** Audio alerts for idle detection
3. **Settings UI:** User-friendly threshold configuration (Task Group 13)
4. **Idle time analytics:** Track idle patterns in reporting (Task Group 12)
5. **Smart thresholds:** ML-based threshold recommendations
6. **Multiple timers:** Handle concurrent timers (if feature added)

## Related Documentation

- **Task Group 9 Completion:** See `TASK_GROUP_9_COMPLETION.md`
- **Celery Configuration:** See `workstate/settings.py`
- **API Reference:** See `time_tracking/views/idle_views.py`
- **Model Reference:** See `time_tracking/models.py`
- **Frontend Component:** See `templates/time_tracking/components/idle_notification.html`
