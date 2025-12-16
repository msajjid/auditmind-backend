import uuid
from django.db import models


class ClassifierOutput(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    evidence = models.ForeignKey(
        "Evidence",
        on_delete=models.CASCADE,
        related_name="classifier_outputs",
        db_column="evidence_id",
    )
    pipeline_run = models.ForeignKey(
        "AiPipelineRun",
        on_delete=models.CASCADE,
        related_name="classifier_outputs",
        db_column="pipeline_run_id",
    )
    primary_controls = models.JSONField()          # list[str]
    confidence = models.FloatField()
    raw_output = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "classifier_outputs"

    def __str__(self) -> str:
        return f"ClassifierOutput({self.id})"