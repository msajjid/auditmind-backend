from django.utils import timezone

from audit_api.agents.base import BaseAgent
from audit_api.models import Evidence, AiPipelineRun, ClassifierOutput
from audit_api.services.control_search_service import ControlSearchService
from audit_api.services.task_auto_create_service import TaskAutoCreateService
from audit_api.services.preprocessing_service import EvidencePreprocessingService
from audit_api.services.embedding_service import EmbeddingService
from audit_api.services.classification_cache_service import ClassificationCacheService


class EvidenceClassifierAgent(BaseAgent):
    name = "evidence-classifier"
    version = "0.2.0-fts"

    def __init__(self):
        self.search = ControlSearchService()
        self.tasks = TaskAutoCreateService()
        self.preprocessing = EvidencePreprocessingService()
        self.embedding = EmbeddingService()
        self.cache = ClassificationCacheService(self.embedding)
        self.cache_threshold = 0.30  # L2 distance on normalized vectors

    def classify(self, evidence: Evidence) -> dict:
        now = timezone.now()

        # 1) Preprocessing must exist
        parts = [
            evidence.title or "",
            evidence.description or "",
            evidence.evidence_type_id or "",
            evidence.source_type_id or "",
            evidence.extracted_text or "",
        ]
        text = "\n".join([p for p in parts if p]).strip()
        hints = []
        if (evidence.source_type_id or "").lower() in {"aws_s3", "aws"}:
            hints.append("iam policy permissions access control authorization")
        if "s3:" in (evidence.extracted_text or "").lower():
            hints.append("iam policy s3 access control authorization")
        text = text + "\n" + " ".join(hints)

        content_hash = self.preprocessing.content_hash(text)

        # Cache lookup (exact hash or vector similarity)
        cached = self.cache.find_cached(text=text, content_hash=content_hash)
        if cached:
            pipeline_run = AiPipelineRun.objects.create(
                pipeline_type="evidence_classification",
                status="completed",
                started_at=now,
                finished_at=timezone.now(),
                details={
                    "cache_hit": True,
                    "similarity": cached.get("similarity"),
                    "source_evidence_id": cached.get("source_evidence_id"),
                    "agent": self.name,
                    "version": self.version,
                },
            )
            classification = {
                "evidence_id": str(evidence.id),
                "primary_controls": cached.get("primary_controls", []),
                "confidence": float(cached.get("confidence", 0.0)),
                "pipeline_run_id": str(pipeline_run.id),
                "stub": False,
                "cache_hit": True,
                "similarity": cached.get("similarity"),
                "source_evidence_id": cached.get("source_evidence_id"),
            }
            evidence.ai_classification = classification
            evidence.save(update_fields=["ai_classification"])
            return classification

        pipeline_run = AiPipelineRun.objects.create(
            pipeline_type="evidence_classification",
            status="running",
            started_at=now,
            details={
                "steps": [
                    "preprocessing",
                    "candidate_retrieval_fts",
                    "control_ranking",
                    "thresholding",
                    "persistence",
                    "auto_task_creation",
                ],
                "agent": self.name,
                "version": self.version,
                "cache_hit": False,
            },
        )

        # 2) Candidate retrieval (SOC2 controls table)
        candidates = self.search.top_candidates(text=text, limit=5)

        # 3) Thresholding (simple + deterministic)
        # If nothing found, fall back to GENERIC so pipeline still works.
        threshold = 0.01
        selected = [c for c in candidates if c.score >= threshold]
        if not selected:
            primary_controls = ["control:GENERIC"]
            confidence = 0.8
            matched_controls = []
            raw = {
                "reason": "No FTS candidates above threshold; fallback to GENERIC.",
                "threshold": threshold,
                "candidate_count": len(candidates),
            }
        else:
            # store references as primary controls for now (human-readable)
            primary_controls = [c.control.reference for c in selected[:3]]
            confidence = min(0.95, 0.5 + (selected[0].score * 0.5))
            matched_controls = [c.control for c in selected[:3]]
            raw = {
                "threshold": threshold,
                "candidates": [
                    {"id": str(c.control.id), "reference": c.control.reference, "score": c.score}
                    for c in candidates
                ],
            }

        # 4) Persist classifier output
        ClassifierOutput.objects.create(
            evidence=evidence,
            pipeline_run=pipeline_run,
            primary_controls=primary_controls,
            confidence=float(confidence),
            raw_output=raw,
        )

        # 5) Auto-create tasks (only for real controls)
        created_tasks = self.tasks.create_tasks_for_controls(
            evidence=evidence,
            controls=matched_controls,
        )

        # 6) Evidence ai_classification
        pipeline_run.status = "completed"
        pipeline_run.finished_at = timezone.now()
        pipeline_run.details = {
            **(pipeline_run.details or {}),
            "result": {
                "primary_controls": primary_controls,
                "confidence": float(confidence),
                "created_tasks": [str(t.id) for t in created_tasks],
            },
        }
        pipeline_run.save(update_fields=["status", "finished_at", "details", "updated_at"])

        # 6b) Store embedding for future cache hits
        self.cache.store_embedding(
            evidence=evidence,
            text=text,
            content_hash=content_hash,
        )

        evidence.ai_classification = {
            "primary_controls": primary_controls,
            "confidence": float(confidence),
            "pipeline_run_id": str(pipeline_run.id),
            "created_tasks": [str(t.id) for t in created_tasks],
            "stub": False,
            "cache_hit": False,
            "content_hash": content_hash,
        }
        evidence.save(update_fields=["ai_classification"])

        return {
            "evidence_id": str(evidence.id),
            "primary_controls": primary_controls,
            "confidence": float(confidence),
            "pipeline_run_id": str(pipeline_run.id),
            "stub": False,
            "cache_hit": False,
        }
