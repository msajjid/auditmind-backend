import uuid
from django.db import models


class ModelRegistry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    model_type = models.CharField(max_length=50, default="llm")  # llm | embedding
    embedding_dims = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "model_registry"
        unique_together = ("name", "version", "provider")

    def __str__(self) -> str:
        return f"{self.name}@{self.version} ({self.provider})"
