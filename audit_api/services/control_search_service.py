from dataclasses import dataclass
from typing import List

from django.contrib.postgres.search import (
    SearchVector,
    SearchQuery,
    SearchRank,
)
from audit_api.models import Control


@dataclass
class ControlCandidate:
    control: Control
    score: float


class ControlSearchService:
    """
    Postgres full-text search over controls.
    Tuned for small SOC2 dataset + JSON-ish evidence text.
    """

    def top_candidates(self, *, text: str, limit: int = 5) -> List[ControlCandidate]:
        text = (text or "").strip()
        if not text:
            return []

        # Weighted vector: description matters most
        vector = (
            SearchVector("reference", weight="A")
            + SearchVector("title", weight="B")
            + SearchVector("description", weight="A")
        )

        # websearch handles “IAM policy S3” better than plain
        query = SearchQuery(text, search_type="websearch")

        qs = (
            Control.objects.annotate(rank=SearchRank(vector, query))
            .filter(rank__gt=0.0)
            .order_by("-rank")[:limit]
        )

        return [ControlCandidate(control=c, score=float(c.rank)) for c in qs]
