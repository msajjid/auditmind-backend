from typing import Optional, Dict, Any
from uuid import UUID

from pgvector.django import L2Distance
from audit_api.models import EvidenceEmbedding, Evidence, ClassifierOutput
from audit_api.services.embedding_service import EmbeddingService


class ClassificationCacheService:
    """
    Caches classifier results by embedding similarity and content hash.
    """

    def __init__(self, embedding_service: EmbeddingService | None = None, *, threshold: float = 0.30):
        self.embedding_service = embedding_service or EmbeddingService()
        self.threshold = threshold  # L2 distance threshold on normalized vectors

    def _build_response(self, evidence: Evidence, *, similarity: float, source: Evidence) -> Optional[Dict[str, Any]]:
        classification = evidence.ai_classification
        if not classification:
            latest = evidence.classifier_outputs.order_by("-created_at").first()
            if not latest:
                return None
            classification = {
                "primary_controls": latest.primary_controls,
                "confidence": float(latest.confidence),
                "pipeline_run_id": str(latest.pipeline_run_id),
                "stub": False,
            }

        return {
            **classification,
            "cache_hit": True,
            "similarity": similarity,
            "source_evidence_id": str(source.id),
        }

    def find_cached(self, *, text: str, content_hash: str) -> Optional[Dict[str, Any]]:
        # 1) Exact hash match (deterministic reuse)
        emb = (
            EvidenceEmbedding.objects.select_related("evidence")
            .filter(content_hash=content_hash)
            .order_by("-created_at")
            .first()
        )
        if emb:
            resp = self._build_response(emb.evidence, similarity=1.0, source=emb.evidence)
            if resp:
                return resp

        # 2) Vector similarity search
        vector = self.embedding_service.embed_vector(text)
        candidate = (
            EvidenceEmbedding.objects.select_related("evidence")
            .annotate(distance=L2Distance("vector", vector))
            .filter(distance__lte=self.threshold)
            .order_by("distance")
            .first()
        )
        if candidate:
            resp = self._build_response(
                candidate.evidence,
                similarity=max(0.0, 1.0 - float(candidate.distance)),
                source=candidate.evidence,
            )
            if resp:
                return resp

        return None

    def store_embedding(
        self,
        *,
        evidence: Evidence,
        text: str,
        content_hash: str,
    ) -> EvidenceEmbedding:
        return self.embedding_service.upsert_embedding(
            evidence=evidence,
            text=text,
            content_hash=content_hash,
        )
