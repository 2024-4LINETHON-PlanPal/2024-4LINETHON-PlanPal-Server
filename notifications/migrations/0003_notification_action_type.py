# Generated by Django 5.0.7 on 2024-11-07 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_reply'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='action_type',
            field=models.CharField(default='read', max_length=50),
        ),
    ]