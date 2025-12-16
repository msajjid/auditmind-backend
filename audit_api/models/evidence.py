import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField


class Evidence(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    organization = models.ForeignKey(
        "Organization",
        on_delete=models.CASCADE,
        related_name="evidence",
        db_column="organization_id",
    )
    control = models.ForeignKey(
        "Control",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evidence_items",
        db_column="control_id",
    )
    uploaded_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_evidence",
        db_column="uploaded_by",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    evidence_type_id = models.CharField(max_length=100, null=True, blank=True)
    source_type_id = models.CharField(max_length=100, null=True, blank=True)
    storage_path = models.CharField(max_length=1024)
    file_size = models.BigIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, default="uploaded")
    extracted_text = models.TextField(null=True, blank=True)
    ai_classification = models.JSONField(null=True, blank=True)
    tags = ArrayField(
        base_field=models.CharField(max_length=255),
        null=True,
        blank=True,
    )
    collected_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evidence"

    def __str__(self) -> str:
        return self.title