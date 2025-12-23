import uuid
from django.db import models


class AgentStepLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_run = models.ForeignKey(
        "AgentRun",
        on_delete=models.CASCADE,
        related_name="step_logs",
        db_column="agent_run_id",
    )
    step_name = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default="running")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    input_snapshot = models.JSONField(null=True, blank=True)
    output_snapshot = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "agent_step_logs"

    def __str__(self) -> str:
        return f"{self.step_name} [{self.status}]"
