import uuid
from django.db import models
from pgvector.django import VectorField


class EvidenceEmbedding(models.Model):
    """
    Stores embeddings for evidence text to enable cached classification.
    One row per (evidence, model_name, content_hash); updated on re-classify.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidence = models.ForeignKey(
        "Evidence",
        on_delete=models.CASCADE,
        related_name="embeddings",
        db_column="evidence_id",
    )
    vector = VectorField(dimensions=128)  # Adjust dimensions if you swap in a real embedding model
    model_name = models.CharField(max_length=100, default="hash-embed-128")
    content_hash = models.CharField(max_length=64)  # sha256 hex
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evidence_embeddings"
        unique_together = ("evidence", "model_name", "content_hash")

    def __str__(self) -> str:
        return f"Embedding({self.evidence_id}, {self.model_name})"
