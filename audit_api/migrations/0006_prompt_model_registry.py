import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit_api", "0005_org_membership_viewer"),
    ]

    operations = [
        migrations.CreateModel(
            name="PromptTemplate",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("version", models.CharField(max_length=50)),
                ("content", models.TextField()),
                ("metadata", models.JSONField(null=True, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "prompt_templates",
                "unique_together": {("name", "version")},
            },
        ),
        migrations.CreateModel(
            name="ModelRegistry",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("provider", models.CharField(max_length=100)),
                ("version", models.CharField(max_length=50)),
                ("model_type", models.CharField(max_length=50, default="llm")),
                ("embedding_dims", models.IntegerField(null=True, blank=True)),
                ("metadata", models.JSONField(null=True, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "model_registry",
                "unique_together": {("name", "version", "provider")},
            },
        ),
    ]
