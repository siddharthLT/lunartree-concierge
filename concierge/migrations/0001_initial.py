from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ConciergeRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_type', models.CharField(choices=[
                    ('coffee', 'Coffee'),
                    ('bagel', 'Bagel'),
                    ('eddie_merlots_reservation', "Eddie Merlot's reservation"),
                    ('experience_biolens', 'Experience BioLens'),
                    ('workspace_request', 'Workspace request'),
                ], max_length=40)),
                ('guest_name', models.CharField(blank=True, max_length=200)),
                ('organization', models.CharField(blank=True, max_length=200)),
                ('role', models.CharField(blank=True, max_length=50)),
                ('details', models.JSONField(blank=True, default=dict)),
                ('status', models.CharField(choices=[
                    ('pending', 'Pending'),
                    ('in_progress', 'In progress'),
                    ('fulfilled', 'Fulfilled'),
                ], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
