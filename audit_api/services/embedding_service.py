import hashlib
from typing import List, Tuple

from audit_api.models import Evidence, EvidenceEmbedding


class EmbeddingService:
    """
    Deterministic, local embedding stub.
    Replace `embed_vector` with a real embedding provider (OpenAI, Cohere, etc.)
    but keep the vector length stable with the model_dim constant.
    """

    model_name = "hash-embed-128"
    model_dim = 128

    def embed_vector(self, text: str) -> List[float]:
        text = (text or "").strip()
        if not text:
            return [0.0] * self.model_dim

        # Hash-based pseudo-embedding (repeat hash to fill dim)
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        floats: List[float] = []
        while len(floats) < self.model_dim:
            for b in digest:
                floats.append((b / 255.0) * 2 - 1)  # scale to [-1, 1]
                if len(floats) == self.model_dim:
                    break
            digest = hashlib.sha256(digest).digest()

        # L2 normalize so pgvector distances are meaningful
        norm = sum(x * x for x in floats) ** 0.5 or 1.0
        return [x / norm for x in floats]

    def upsert_embedding(
        self,
        *,
        evidence: Evidence,
        text: str,
        content_hash: str,
    ) -> EvidenceEmbedding:
        vector = self.embed_vector(text)
        embedding, _ = EvidenceEmbedding.objects.update_or_create(
            evidence=evidence,
            model_name=self.model_name,
            content_hash=content_hash,
            defaults={"vector": vector},
        )
        return embedding

    def vector_and_hash(self, text: str) -> Tuple[List[float], str]:
        text = (text or "").strip()
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return self.embed_vector(text), content_hash
