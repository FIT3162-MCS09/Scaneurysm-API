# Generated by Django 5.1.7 on 2025-03-10 15:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0003_file'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='file',
            name='id',
        ),
        migrations.AlterField(
            model_name='file',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='models.user'),
        ),
        migrations.DeleteModel(
            name='S3File',
        ),
    ]
