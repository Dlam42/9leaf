# Generated by Django 5.1.5 on 2025-04-18 01:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0002_user_client_firebase_uid_delete_request"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user_client",
            name="firebase_uid",
        ),
        migrations.AddField(
            model_name="user_client",
            name="is_admin",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="Request",
            fields=[
                ("request_id", models.AutoField(primary_key=True, serialize=False)),
                ("request_name", models.CharField(max_length=255)),
                ("start_time", models.CharField(max_length=255)),
                ("tool", models.CharField(max_length=255)),
                ("request_description", models.TextField()),
                ("request_price", models.CharField(max_length=255)),
                ("address", models.CharField(max_length=255)),
                ("city", models.CharField(max_length=255)),
                ("state", models.CharField(max_length=255)),
                ("geo_location", models.CharField(max_length=255)),
                ("unit_apt_num", models.CharField(max_length=255)),
                ("zip_code", models.CharField(max_length=255)),
                ("duration", models.CharField(max_length=255)),
                ("personal_business", models.CharField(max_length=255)),
                ("request_size", models.CharField(max_length=255)),
                ("people_amount", models.CharField(max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("declined", "Declined"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "customer_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="members.customer",
                    ),
                ),
                (
                    "user_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="members.user_client",
                    ),
                ),
            ],
        ),
    ]
