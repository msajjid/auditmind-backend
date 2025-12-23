import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("audit_api", "0003_merge"),
    ]

    operations = [
        migrations.CreateModel(
            name="AgentRun",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("agent_name", models.CharField(max_length=100)),
                ("agent_version", models.CharField(max_length=50, null=True, blank=True)),
                ("status", models.CharField(max_length=50, default="running")),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(null=True, blank=True)),
                ("details", models.JSONField(null=True, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "evidence",
                    models.ForeignKey(
                        db_column="evidence_id",
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="audit_api.evidence",
                        related_name="agent_runs",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "pipeline_run",
                    models.ForeignKey(
                        db_column="pipeline_run_id",
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="audit_api.aipipelinerun",
                        related_name="agent_runs",
                        null=True,
                        blank=True,
                    ),
                ),
            ],
            options={
                "db_table": "agent_runs",
            },
        ),
        migrations.CreateModel(
            name="AgentStepLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("step_name", models.CharField(max_length=100)),
                ("status", models.CharField(max_length=50, default="running")),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(null=True, blank=True)),
                ("input_snapshot", models.JSONField(null=True, blank=True)),
                ("output_snapshot", models.JSONField(null=True, blank=True)),
                ("error", models.TextField(null=True, blank=True)),
                ("metadata", models.JSONField(null=True, blank=True)),
                (
                    "agent_run",
                    models.ForeignKey(
                        db_column="agent_run_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="audit_api.agentrun",
                        related_name="step_logs",
                    ),
                ),
            ],
            options={
                "db_table": "agent_step_logs",
            },
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("event_type", models.CharField(max_length=100)),
                ("payload", models.JSONField(null=True, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "evidence",
                    models.ForeignKey(
                        db_column="evidence_id",
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="audit_api.evidence",
                        related_name="events",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        db_column="organization_id",
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="audit_api.organization",
                        related_name="events",
                        null=True,
                        blank=True,
                    ),
                ),
            ],
            options={
                "db_table": "events",
                "indexes": [
                    models.Index(fields=["event_type"], name="events_event_type_idx"),
                    models.Index(fields=["organization"], name="events_org_idx"),
                    models.Index(fields=["evidence"], name="events_evidence_idx"),
                ],
            },
        ),
    ]
