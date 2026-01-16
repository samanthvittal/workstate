"""
Celery tasks for time tracking background operations.

Handles periodic timer synchronization and idle detection.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from time_tracking.services.cache import TimeEntryCache

logger = logging.getLogger(__name__)


@shared_task(name='time_tracking.sync_active_timers')
def sync_active_timers():
    """
    Periodic task to synchronize Redis cache to PostgreSQL.

    Runs every 60 seconds to ensure timer state remains consistent
    between cache and database.

    Returns:
        dict: Summary of sync operation
    """
    from time_tracking.models import TimeEntry

    try:
        # Get all users with active timers in database
        active_timers = TimeEntry.objects.filter(is_running=True).values_list('user_id', flat=True)
        synced_count = 0
        failed_count = 0

        for user_id in active_timers:
            if TimeEntryCache.sync_to_db(user_id):
                synced_count += 1
            else:
                failed_count += 1

        logger.info(f"Timer sync complete: {synced_count} synced, {failed_count} failed")

        return {
            'synced': synced_count,
            'failed': failed_count,
            'status': 'success'
        }

    except Exception as e:
        logger.error(f"Error during timer sync: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task(name='time_tracking.restore_timers_on_startup')
def restore_timers_on_startup():
    """
    Task to restore active timers from PostgreSQL to Redis on app startup.

    Returns:
        dict: Summary of restore operation
    """
    try:
        restored_count = TimeEntryCache.restore_from_db()

        return {
            'restored': restored_count,
            'status': 'success'
        }

    except Exception as e:
        logger.error(f"Error restoring timers on startup: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task(name='time_tracking.check_idle_timers')
def check_idle_timers():
    """
    Periodic task to detect idle timers and create notifications.

    Runs every 60 seconds. For each active timer, checks if the elapsed time
    exceeds the user's idle threshold. If so, creates an idle notification.

    Returns:
        dict: Summary of idle detection operation
    """
    from time_tracking.models import TimeEntry, UserTimePreferences, IdleTimeNotification

    try:
        # Get all active timers from PostgreSQL
        active_timers = TimeEntry.objects.select_related('user').filter(is_running=True)
        notifications_created = 0
        already_notified = 0

        current_time = timezone.now()

        for timer in active_timers:
            try:
                # Get user's idle threshold (default to 5 minutes if preferences don't exist)
                try:
                    preferences = UserTimePreferences.objects.get(user=timer.user)
                    idle_threshold_minutes = preferences.idle_threshold_minutes
                except UserTimePreferences.DoesNotExist:
                    idle_threshold_minutes = 5  # Default value

                # Skip if idle detection disabled (threshold is 0)
                if idle_threshold_minutes <= 0:
                    continue

                # Calculate elapsed time
                if not timer.start_time:
                    continue

                elapsed_time = current_time - timer.start_time
                elapsed_minutes = elapsed_time.total_seconds() / 60

                # Check if timer is idle
                if elapsed_minutes > idle_threshold_minutes:
                    # Calculate when idle period started
                    idle_start_time = timer.start_time + timedelta(minutes=idle_threshold_minutes)

                    # Check if notification already exists for this timer
                    existing_notification = IdleTimeNotification.objects.filter(
                        time_entry=timer,
                        action_taken='none'
                    ).first()

                    if existing_notification:
                        already_notified += 1
                        continue

                    # Create idle notification
                    IdleTimeNotification.objects.create(
                        user=timer.user,
                        time_entry=timer,
                        idle_start_time=idle_start_time
                    )
                    notifications_created += 1
                    logger.info(f"Created idle notification for timer {timer.id} (user: {timer.user.email})")

            except Exception as e:
                logger.error(f"Error processing timer {timer.id}: {e}")
                continue

        logger.info(f"Idle detection complete: {notifications_created} notifications created, {already_notified} already notified")

        return {
            'notifications_created': notifications_created,
            'already_notified': already_notified,
            'status': 'success'
        }

    except Exception as e:
        logger.error(f"Error during idle detection: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }
