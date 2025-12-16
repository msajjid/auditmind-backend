# Generated manually: adds pgvector extension and EvidenceEmbedding model.
import uuid
from django.db import migrations, models
import django.db.models.deletion
import pgvector.django


def create_vector_extension(apps, schema_editor):
    schema_editor.execute("CREATE EXTENSION IF NOT EXISTS vector;")


class Migration(migrations.Migration):

    dependencies = [
        ("audit_api", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_vector_extension, reverse_code=migrations.RunPython.noop),
        migrations.CreateModel(
            name="EvidenceEmbedding",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("vector", pgvector.django.VectorField(dimensions=128)),
                ("model_name", models.CharField(max_length=100, default="hash-embed-128")),
                ("content_hash", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "evidence",
                    models.ForeignKey(
                        db_column="evidence_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="embeddings",
                        to="audit_api.evidence",
                    ),
                ),
            ],
            options={
                "db_table": "evidence_embeddings",
                "unique_together": {("evidence", "model_name", "content_hash")},
            },
        ),
    ]
