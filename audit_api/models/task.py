import uuid
from django.db import models


class Task(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    organization = models.ForeignKey(
        "Organization",
        on_delete=models.CASCADE,
        related_name="tasks",
        db_column="organization_id",
    )
    framework = models.ForeignKey(
        "Framework",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        db_column="framework_id",
    )
    control = models.ForeignKey(
        "Control",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        db_column="control_id",
    )
    evidence = models.ForeignKey(
        "Evidence",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        db_column="evidence_id",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, default="open")
    assignee = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        db_column="assignee_id",
    )
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tasks"

    def __str__(self) -> str:
        return self.title
