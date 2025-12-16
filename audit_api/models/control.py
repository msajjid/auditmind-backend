import uuid
from django.db import models


class Control(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    framework = models.ForeignKey(
        "Framework",
        on_delete=models.CASCADE,
        related_name="controls",
        db_column="framework_id",
    )
    reference = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    risk_level = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "controls"

    def __str__(self) -> str:
        return f"{self.reference} - {self.title}"