# Generated by Django 5.2.1 on 2025-05-08 20:16

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='StatementData',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('pdf_filename', models.CharField(
                    blank=True, max_length=255, null=True)),
                ('uploaded_at', models.DateTimeField(
                    default=django.utils.timezone.now)),
                ('extracted_data', models.JSONField()),
            ],
            options={
                'verbose_name_plural': 'Statement Data Records',
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
