import uuid
from django.db import models


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100)
    evidence = models.ForeignKey(
        "Evidence",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        db_column="evidence_id",
    )
    organization = models.ForeignKey(
        "Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        db_column="organization_id",
    )
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "events"
        indexes = [
            models.Index(fields=["event_type"], name="events_event_type_idx"),
            models.Index(fields=["organization"], name="events_org_idx"),
            models.Index(fields=["evidence"], name="events_evidence_idx"),
        ]

    def __str__(self) -> str:
        return self.event_type
