import uuid
from django.db import models


class AiPipelineRun(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    pipeline_type = models.CharField(max_length=100)    # e.g. "evidence_classification"
    status = models.CharField(max_length=50, default="pending")
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_pipeline_runs"

    def __str__(self) -> str:
        return f"{self.pipeline_type} [{self.status}]"