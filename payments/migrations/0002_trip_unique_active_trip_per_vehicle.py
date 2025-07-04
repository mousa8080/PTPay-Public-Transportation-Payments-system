# Generated by Django 5.1.7 on 2025-04-30 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="trip",
            constraint=models.UniqueConstraint(
                condition=models.Q(("end_time__isnull", True)),
                fields=("vehicle",),
                name="unique_active_trip_per_vehicle",
            ),
        ),
    ]
