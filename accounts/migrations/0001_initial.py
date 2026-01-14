# Generated migration for UserProfile model

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True,
                    related_name='profile',
                    serialize=False,
                    to=settings.AUTH_USER_MODEL
                )),
                ('full_name', models.CharField(
                    blank=True,
                    help_text="User's full name",
                    max_length=200
                )),
                ('avatar', models.ImageField(
                    blank=True,
                    help_text='User avatar image',
                    null=True,
                    upload_to='avatars/%Y/%m/',
                    validators=[django.core.validators.FileExtensionValidator(
                        allowed_extensions=['jpg', 'jpeg', 'png', 'gif']
                    )]
                )),
                ('job_title', models.CharField(
                    blank=True,
                    help_text="User's job title",
                    max_length=100
                )),
                ('company', models.CharField(
                    blank=True,
                    help_text="User's company name",
                    max_length=100
                )),
                ('phone_number', models.CharField(
                    blank=True,
                    help_text="User's phone number",
                    max_length=20
                )),
                ('timezone', models.CharField(
                    default='UTC',
                    help_text="User's timezone for displaying dates and times",
                    max_length=50,
                    choices=[('UTC', 'UTC')]  # Full choices set in model
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    help_text='Timestamp when profile was created'
                )),
                ('updated_at', models.DateTimeField(
                    auto_now=True,
                    help_text='Timestamp when profile was last updated'
                )),
            ],
            options={
                'verbose_name': 'User Profile',
                'verbose_name_plural': 'User Profiles',
                'db_table': 'user_profiles',
            },
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['user'], name='profile_user_idx'),
        ),
    ]
