# Generated by Django 5.2 on 2025-06-15 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0008_remove_route_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="driver",
            name="uid",
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]
