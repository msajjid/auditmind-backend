from audit_api.agents.base import BaseAgent
from audit_api.models import Evidence, ClassifierOutput
from audit_api.services.control_search_service import ControlSearchService
from audit_api.services.task_auto_create_service import TaskAutoCreateService
from audit_api.services.preprocessing_service import EvidencePreprocessingService
from audit_api.services.embedding_service import EmbeddingService
from audit_api.services.classification_cache_service import ClassificationCacheService
from audit_api.services.pipeline_logging_service import PipelineLogger
from audit_api.services.llm_validation_service import LLMValidationService


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
        self.validator = LLMValidationService()

    def classify(self, evidence: Evidence) -> dict:
        step_names = [
            "preprocessing",
            "cache_lookup",
            "candidate_retrieval_fts",
            "control_ranking",
            "thresholding",
            "llm_validation",
            "persistence",
            "auto_task_creation",
            "embedding_store",
        ]

        logger = PipelineLogger(
            pipeline_type="evidence_classification",
            agent_name=self.name,
            agent_version=self.version,
            evidence=evidence,
        )
        pipeline_run = logger.start(
            step_names=step_names,
            initial_details={
                "cache_hit": False,
                "model": {"name": "hash-embed-128", "provider": "local", "version": "1.0"},
                "prompt_template": {"name": "classifier-default", "version": "1.0"},
            },
        )

        try:
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
            preprocess_log = logger.start_step(
                "preprocessing",
                input_snapshot={
                    "evidence_id": str(evidence.id),
                    "has_text": bool(text),
                    "hint_count": len(hints),
                },
            )
            logger.complete_step(
                preprocess_log,
                output_snapshot={"content_hash": content_hash, "text_chars": len(text)},
            )
            logger.emit_event(
                "EvidencePreprocessed",
                payload={
                    "evidence_id": str(evidence.id),
                    "pipeline_run_id": str(pipeline_run.id),
                    "content_hash": content_hash,
                    "text_chars": len(text),
                },
            )

            # Cache lookup (exact hash or vector similarity)
            cache_log = logger.start_step(
                "cache_lookup",
                input_snapshot={"content_hash": content_hash},
            )
            cached = self.cache.find_cached(text=text, content_hash=content_hash)
            if cached:
                logger.complete_step(
                    cache_log,
                    output_snapshot={
                        "cache_hit": True,
                        "similarity": cached.get("similarity"),
                        "source_evidence_id": cached.get("source_evidence_id"),
                    },
                )
                logger.finish_pipeline(
                    status="completed",
                    details={
                        "cache_hit": True,
                        "similarity": cached.get("similarity"),
                        "source_evidence_id": cached.get("source_evidence_id"),
                    },
                )
                classification = {
                    "evidence_id": str(evidence.id),
                    "primary_controls": cached.get("primary_controls", []),
                    "confidence": float(cached.get("confidence", 0.0)),
                    "pipeline_run_id": str(pipeline_run.id),
                    "agent_run_id": str(logger.agent_run.id),
                    "stub": False,
                    "cache_hit": True,
                    "similarity": cached.get("similarity"),
                    "source_evidence_id": cached.get("source_evidence_id"),
                }
                evidence.ai_classification = classification
                evidence.save(update_fields=["ai_classification"])
                return classification
            logger.complete_step(cache_log, output_snapshot={"cache_hit": False})

            # 2) Candidate retrieval (SOC2 controls table)
            retrieval_log = logger.start_step(
                "candidate_retrieval_fts",
                input_snapshot={"text_chars": len(text), "limit": 5},
            )
            candidates = self.search.top_candidates(text=text, limit=5)
            logger.complete_step(
                retrieval_log,
                output_snapshot={
                    "candidate_count": len(candidates),
                    "candidates": [
                        {"reference": c.control.reference, "score": c.score}
                        for c in candidates
                    ],
                },
            )

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

            ranking_log = logger.start_step(
                "control_ranking",
                input_snapshot={"threshold": threshold},
            )
            logger.complete_step(
                ranking_log,
                output_snapshot={
                    "selected_controls": primary_controls,
                    "matched_count": len(matched_controls),
                },
            )

            threshold_log = logger.start_step(
                "thresholding",
                input_snapshot={"threshold": threshold},
            )
            logger.complete_step(
                threshold_log,
                output_snapshot={
                    "passed": bool(selected),
                    "fallback_to_generic": not bool(selected),
                },
            )

            # 3b) Optional LLM validation (stub)
            validation_log = logger.start_step(
                "llm_validation",
                input_snapshot={
                    "primary_controls": primary_controls,
                    "initial_confidence": float(confidence),
                },
            )
            validated_confidence, validation_justification = self.validator.validate(
                text=text,
                control_references=primary_controls,
                confidence=float(confidence),
            )
            logger.complete_step(
                validation_log,
                output_snapshot={
                    "validated_confidence": float(validated_confidence),
                    "justification": validation_justification,
                },
            )
            confidence = float(validated_confidence)

            # 4) Persist classifier output
            persist_log = logger.start_step(
                "persistence",
                input_snapshot={
                    "primary_controls": primary_controls,
                    "confidence": float(confidence),
                },
            )
            ClassifierOutput.objects.create(
                evidence=evidence,
                pipeline_run=pipeline_run,
                primary_controls=primary_controls,
                confidence=float(confidence),
                raw_output=raw,
            )
            logger.complete_step(
                persist_log,
                output_snapshot={"primary_controls": primary_controls, "confidence": float(confidence)},
            )

            logger.emit_event(
                "ClassificationCompleted",
                payload={
                    "evidence_id": str(evidence.id),
                    "pipeline_run_id": str(pipeline_run.id),
                    "primary_controls": primary_controls,
                    "confidence": float(confidence),
                },
            )

            # 5) Auto-create tasks (only for real controls)
            tasks_log = logger.start_step("auto_task_creation", input_snapshot={"control_count": len(matched_controls)})
            created_tasks = self.tasks.create_tasks_for_controls(
                evidence=evidence,
                controls=matched_controls,
            )
            logger.complete_step(
                tasks_log,
                output_snapshot={"created_task_ids": [str(t.id) for t in created_tasks]},
            )

            # 6) Evidence ai_classification
            logger.finish_pipeline(
                status="completed",
                details={
                    "result": {
                        "primary_controls": primary_controls,
                        "confidence": float(confidence),
                        "created_tasks": [str(t.id) for t in created_tasks],
                    }
                },
            )

            # 6b) Store embedding for future cache hits
            embed_log = logger.start_step(
                "embedding_store",
                input_snapshot={"content_hash": content_hash},
            )
            self.cache.store_embedding(
                evidence=evidence,
                text=text,
                content_hash=content_hash,
            )
            logger.complete_step(
                embed_log,
                output_snapshot={"content_hash": content_hash, "stored": True},
            )
            logger.emit_event(
                "EmbeddingComputed",
                payload={
                    "evidence_id": str(evidence.id),
                    "pipeline_run_id": str(pipeline_run.id),
                    "content_hash": content_hash,
                },
            )

            evidence.ai_classification = {
                "primary_controls": primary_controls,
                "confidence": float(confidence),
                "pipeline_run_id": str(pipeline_run.id),
                "agent_run_id": str(logger.agent_run.id),
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
                "agent_run_id": str(logger.agent_run.id),
                "stub": False,
                "cache_hit": False,
            }
        except Exception as exc:
            logger.finish_pipeline(status="failed", details={"error": str(exc)})
            raise
