# Redis & Celery Setup Guide

This guide explains why and when Redis and Celery are needed in Workstate, how to set them up for local development, and how the application handles their absence.

## Table of Contents

- [Why Redis and Celery?](#why-redis-and-celery)
- [What Features Require Redis/Celery?](#what-features-require-rediscelery)
- [Graceful Degradation](#graceful-degradation)
- [Local Development Setup](#local-development-setup)
- [Production Setup](#production-setup)
- [Troubleshooting](#troubleshooting)

## Why Redis and Celery?

### Redis

**Redis** is an in-memory data store used in Workstate for two primary purposes:

1. **Caching Active Timers**: Provides fast access to running timer state without database queries
2. **WebSocket Channel Layer**: Powers real-time cross-tab synchronization for timer updates

**Benefits:**
- Sub-millisecond response times for active timer lookups
- Real-time updates across multiple browser tabs/windows
- Reduced database load during active time tracking

### Celery

**Celery** is a distributed task queue used for background processing:

1. **Celery Worker**: Executes async tasks like report generation and data exports
2. **Celery Beat**: Scheduled task runner for periodic operations (idle timer detection)

**Benefits:**
- Offloads long-running tasks from web requests
- Automatic idle timer detection every 5 minutes
- Scheduled cleanup and maintenance tasks

## What Features Require Redis/Celery?

### Full Functionality (Redis + Celery Running)

✅ **All Features Available:**
- Real-time timer updates across browser tabs
- Cross-tab timer synchronization (start timer in one tab, see it in all tabs)
- Fast active timer display
- Automatic idle timer detection
- Background report generation
- Scheduled cleanup tasks

### Degraded Mode (Redis/Celery NOT Running)

⚠️ **Limited Functionality:**
- ✅ Basic timer operations work (start, stop, discard)
- ✅ Manual time entry creation and editing
- ✅ Time entry list and filtering
- ✅ Analytics dashboard
- ❌ NO cross-tab synchronization (refresh required to see timer state)
- ❌ NO automatic idle detection
- ❌ Slower active timer lookups (database fallback)
- ❌ NO background task processing

**The application will continue to function, but with reduced real-time capabilities.**

## Graceful Degradation

Workstate is designed to handle Redis/Celery unavailability gracefully:

### Cache Service Fallback

When Redis is unavailable, the cache service automatically falls back to the database:

```python
# time_tracking/services/cache.py
def get_active_timer(self, user_id):
    """Get active timer from cache or database fallback."""
    try:
        # Try Redis first
        return self._get_from_redis(user_id)
    except ConnectionError:
        # Fall back to database
        logger.warning("Redis unavailable, falling back to database")
        return self._get_from_database(user_id)
```

### WebSocket Connection Handling

WebSocket connections accept even when Redis channel layer is unavailable:

```python
# time_tracking/consumers.py
async def connect(self):
    try:
        await self.channel_layer.group_add(...)
        await self.accept()
    except Exception as e:
        logger.error("Redis unavailable, accepting connection in degraded mode")
        # Accept connection anyway - basic functionality still works
        await self.accept()
```

### Timer View Resilience

Timer views handle cache errors gracefully:

```python
# time_tracking/views/timer_views.py
try:
    cache_service.set_active_timer(user.id, timer)
except Exception as e:
    logger.error("Cache error, continuing without caching")
    # Timer operation continues successfully
```

## Local Development Setup

### Quick Start

1. **Install Redis:**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# macOS (Homebrew)
brew install redis

# Check installation
redis-cli --version
```

2. **Start Redis Server:**

```bash
# Start Redis in foreground (for testing)
redis-server

# Or start as background service
sudo systemctl start redis-server  # Ubuntu/Debian
brew services start redis          # macOS

# Verify Redis is running
redis-cli ping
# Expected output: PONG
```

3. **Start Celery Worker:**

```bash
# From project root
celery -A workstate worker --loglevel=info
```

4. **Start Celery Beat (for scheduled tasks):**

```bash
# In a separate terminal
celery -A workstate beat --loglevel=info
```

### Development Workflow

**Option 1: Full Stack (Recommended for Time Tracking Development)**

Run all three services in separate terminals:

```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A workstate worker --loglevel=info

# Terminal 3: Celery Beat
celery -A workstate beat --loglevel=info
```

**Option 2: Django Only (Basic Development)**

If you're not working on time tracking features, you can run just Django:

```bash
python manage.py runserver
```

The app will work in degraded mode (no real-time updates, no background tasks).

### Startup Script

Create a convenience script to start all services:

```bash
#!/bin/bash
# start_workstate.sh

# Start Redis (if not already running)
sudo systemctl start redis-server || redis-server &

# Start Django
python manage.py runserver &

# Start Celery Worker
celery -A workstate worker --loglevel=info &

# Start Celery Beat
celery -A workstate beat --loglevel=info &

echo "All services started!"
echo "Django: http://localhost:8000"
echo "Stop all: pkill -f 'celery|redis-server|runserver'"
```

Make executable and run:

```bash
chmod +x start_workstate.sh
./start_workstate.sh
```

## Production Setup

### Docker Compose (Recommended)

The project includes a Docker Compose configuration with all services:

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: workstate
      POSTGRES_USER: workstate
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  web:
    build: .
    command: gunicorn workstate.wsgi:application --bind 0.0.0.0:8000
    depends_on:
      - postgres
      - redis

  celery-worker:
    build: .
    command: celery -A workstate worker --loglevel=info
    depends_on:
      - postgres
      - redis

  celery-beat:
    build: .
    command: celery -A workstate beat --loglevel=info
    depends_on:
      - postgres
      - redis
```

Start all services:

```bash
docker-compose up -d
```

### Systemd Services (Alternative)

Create systemd service files for production Linux deployments:

**Redis:**
```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

**Celery Worker:**
```ini
# /etc/systemd/system/celery-worker.service
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/opt/workstate
ExecStart=/opt/workstate/venv/bin/celery -A workstate worker --loglevel=info

[Install]
WantedBy=multi-user.target
```

**Celery Beat:**
```ini
# /etc/systemd/system/celery-beat.service
[Unit]
Description=Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/workstate
ExecStart=/opt/workstate/venv/bin/celery -A workstate beat --loglevel=info

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
```

## Troubleshooting

### Redis Connection Errors

**Symptom:**
```
ConnectionError: Error 111 connecting to 127.0.0.1:6379. Connection refused.
```

**Solutions:**

1. **Check if Redis is running:**
   ```bash
   redis-cli ping
   # Expected: PONG
   ```

2. **Start Redis if stopped:**
   ```bash
   sudo systemctl start redis-server  # Linux
   brew services start redis          # macOS
   redis-server                       # Manual start
   ```

3. **Check Redis configuration:**
   ```bash
   # Verify Redis is listening on correct port
   sudo netstat -tlnp | grep redis
   # Expected: tcp 0.0.0.0:6379 or 127.0.0.1:6379
   ```

4. **Check firewall:**
   ```bash
   # Allow Redis port (if needed)
   sudo ufw allow 6379
   ```

### Celery Not Processing Tasks

**Symptom:**
Tasks are queued but never execute.

**Solutions:**

1. **Check Celery worker is running:**
   ```bash
   ps aux | grep celery
   ```

2. **Check Celery logs:**
   ```bash
   celery -A workstate worker --loglevel=debug
   ```

3. **Verify Redis connection from Celery:**
   ```python
   # Python shell
   from celery import Celery
   app = Celery('workstate')
   app.config_from_object('django.conf:settings', namespace='CELERY')
   i = app.control.inspect()
   i.active()  # Should show worker info
   ```

4. **Restart Celery worker:**
   ```bash
   pkill -f 'celery worker'
   celery -A workstate worker --loglevel=info
   ```

### Cross-Tab Sync Not Working

**Symptom:**
Starting a timer in one tab doesn't update other tabs.

**Solutions:**

1. **Verify Redis is running:**
   ```bash
   redis-cli ping
   ```

2. **Check WebSocket connection in browser:**
   - Open browser dev tools (F12)
   - Go to Network tab
   - Filter by WS (WebSocket)
   - Look for `ws://localhost:8000/ws/timer/`
   - Connection should show "101 Switching Protocols"

3. **Check Django Channels configuration:**
   ```python
   # settings.py
   CHANNEL_LAYERS = {
       "default": {
           "BACKEND": "channels_redis.core.RedisChannelLayer",
           "CONFIG": {
               "hosts": [("127.0.0.1", 6379)],
           },
       },
   }
   ```

4. **Check browser console for WebSocket errors:**
   - Open dev tools → Console
   - Look for WebSocket connection errors

### Idle Detection Not Working

**Symptom:**
Timers never auto-stop when idle.

**Solutions:**

1. **Verify Celery Beat is running:**
   ```bash
   ps aux | grep 'celery beat'
   ```

2. **Check Beat schedule:**
   ```python
   # Python shell
   from celery import Celery
   app = Celery('workstate')
   app.config_from_object('django.conf:settings', namespace='CELERY')
   print(app.conf.beat_schedule)
   # Should show 'detect-idle-timers' task
   ```

3. **Check task logs:**
   ```bash
   # Look for idle detection task execution
   tail -f /var/log/celery/beat.log
   ```

4. **Verify idle detection settings:**
   ```python
   # settings.py
   CELERY_BEAT_SCHEDULE = {
       'detect-idle-timers': {
           'task': 'time_tracking.tasks.detect_idle_timers',
           'schedule': crontab(minute='*/5'),  # Every 5 minutes
       },
   }
   ```

### Performance Issues

**Symptom:**
Slow timer operations or high database load.

**Solutions:**

1. **Check Redis memory usage:**
   ```bash
   redis-cli info memory
   ```

2. **Monitor Redis performance:**
   ```bash
   redis-cli --latency
   # Latency should be < 1ms
   ```

3. **Check Celery queue backlog:**
   ```python
   # Python shell
   from celery import Celery
   app = Celery('workstate')
   i = app.control.inspect()
   print(i.reserved())  # Tasks being processed
   print(i.scheduled())  # Scheduled tasks
   ```

4. **Clear Redis cache if needed:**
   ```bash
   redis-cli FLUSHDB  # WARNING: Clears all cached data
   ```

## When to Run Redis/Celery

### Always Needed

- **Production deployments** - Always run Redis + Celery for full functionality
- **Time tracking feature development** - Essential for testing real-time updates
- **Integration testing** - Required for testing full time tracking workflow

### Optional

- **UI development** - Not needed for template/CSS changes
- **Simple bug fixes** - Can work without Redis/Celery for non-time-tracking issues
- **Initial setup/exploration** - Can explore the app in degraded mode

### Decision Tree

```
Are you working on time tracking features?
├─ YES → Run Redis + Celery + Django
└─ NO → Are you testing cross-tab sync or idle detection?
    ├─ YES → Run Redis + Celery + Django
    └─ NO → Can run Django only (degraded mode OK)
```

## Configuration Reference

### Django Settings

```python
# settings.py

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
REDIS_DB = os.getenv('REDIS_DB', 0)

# Celery Configuration
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Channels (WebSocket) Configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'detect-idle-timers': {
        'task': 'time_tracking.tasks.detect_idle_timers',
        'schedule': crontab(minute='*/5'),
    },
}
```

### Environment Variables

```bash
# .env
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
```

## Additional Resources

- [Redis Documentation](https://redis.io/docs/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Django Channels Documentation](https://channels.readthedocs.io/)
- [Workstate Architecture Documentation](./ARCHITECTURE.md)

## Summary

**TL;DR:**

1. **Redis** = Fast caching + Real-time cross-tab sync
2. **Celery** = Background tasks + Scheduled jobs
3. **Graceful Degradation** = App works without them (limited features)
4. **Development** = Optional for basic work, required for time tracking
5. **Production** = Always run both for full functionality

**Quick Setup:**
```bash
# Start Redis
sudo systemctl start redis-server

# Start Celery
celery -A workstate worker --loglevel=info &
celery -A workstate beat --loglevel=info &

# Start Django
python manage.py runserver
```

The application is designed to be flexible - run the full stack when you need all features, or run Django alone for basic development. Choose based on what you're working on!
