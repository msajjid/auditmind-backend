from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audit_api", "0006_prompt_model_registry"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="evidence",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="tasks",
                to="audit_api.evidence",
                db_column="evidence_id",
            ),
        ),
    ]
