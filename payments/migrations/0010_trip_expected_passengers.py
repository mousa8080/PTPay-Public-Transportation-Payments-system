# Generated by Django 5.2 on 2025-06-15 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0009_driver_uid"),
    ]

    operations = [
        migrations.AddField(
            model_name="trip",
            name="expected_passengers",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
