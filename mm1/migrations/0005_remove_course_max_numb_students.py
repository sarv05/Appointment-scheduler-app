# Generated by Django 4.2.6 on 2023-11-26 06:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mm1', '0004_rename_seating_capacity_room_numb_cabins_per_room'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='max_numb_students',
        ),
    ]
