# Generated migration for IdleTimeNotification model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('time_tracking', '0003_remove_timeentry_positive_duration_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='IdleTimeNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idle_start_time', models.DateTimeField(help_text='When idle period started (timer_start + idle_threshold)')),
                ('notification_sent_at', models.DateTimeField(auto_now_add=True, help_text='When notification was created and sent')),
                ('action_taken', models.CharField(choices=[('none', 'No action taken'), ('keep', 'Keep time'), ('discard', 'Discard idle time'), ('stop_at_idle', 'Stop timer at idle start')], db_index=True, default='none', help_text='Action user took on this notification', max_length=20)),
                ('action_taken_at', models.DateTimeField(blank=True, help_text='When user took action on this notification', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When notification record was created')),
                ('time_entry', models.ForeignKey(help_text='Time entry that was idle', on_delete=django.db.models.deletion.CASCADE, related_name='idle_notifications', to='time_tracking.timeentry')),
                ('user', models.ForeignKey(help_text='User who received this notification', on_delete=django.db.models.deletion.CASCADE, related_name='idle_time_notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Idle Time Notification',
                'verbose_name_plural': 'Idle Time Notifications',
                'db_table': 'idle_time_notifications',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='idletimenotification',
            index=models.Index(fields=['user'], name='idle_notif_user_idx'),
        ),
        migrations.AddIndex(
            model_name='idletimenotification',
            index=models.Index(fields=['time_entry'], name='idle_notif_time_entry_idx'),
        ),
        migrations.AddIndex(
            model_name='idletimenotification',
            index=models.Index(fields=['action_taken'], name='idle_notif_action_idx'),
        ),
        migrations.AddIndex(
            model_name='idletimenotification',
            index=models.Index(fields=['user', 'action_taken'], name='idle_notif_user_action_idx'),
        ),
    ]
