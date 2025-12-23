import uuid
from django.db import models


class AgentRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_name = models.CharField(max_length=100)
    agent_version = models.CharField(max_length=50, null=True, blank=True)
    pipeline_run = models.ForeignKey(
        "AiPipelineRun",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_runs",
        db_column="pipeline_run_id",
    )
    evidence = models.ForeignKey(
        "Evidence",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_runs",
        db_column="evidence_id",
    )
    status = models.CharField(max_length=50, default="running")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agent_runs"

    def __str__(self) -> str:
        return f"{self.agent_name} [{self.status}]"
