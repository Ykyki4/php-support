# Generated by Django 4.1.7 on 2023-02-24 13:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='type',
        ),
    ]
