from typing import Any, Iterable, Optional

from django.utils import timezone

from audit_api.models import (
    AiPipelineRun,
    AgentRun,
    AgentStepLog,
    Event,
    Evidence,
)


class PipelineLogger:
    """Small helper to persist pipeline + agent run + step logs + events."""

    def __init__(
        self,
        *,
        pipeline_type: str,
        agent_name: str,
        agent_version: str,
        evidence: Optional[Evidence],
    ) -> None:
        self.pipeline_type = pipeline_type
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.evidence = evidence
        self.pipeline_run: AiPipelineRun | None = None
        self.agent_run: AgentRun | None = None

    def start(
        self,
        *,
        step_names: Optional[Iterable[str]] = None,
        initial_details: Optional[dict[str, Any]] = None,
        cache_hit: bool = False,
    ) -> AiPipelineRun:
        now = timezone.now()
        details = {
            "steps": list(step_names) if step_names else [],
            "agent": self.agent_name,
            "version": self.agent_version,
            "cache_hit": cache_hit,
            **(initial_details or {}),
        }
        self.pipeline_run = AiPipelineRun.objects.create(
            pipeline_type=self.pipeline_type,
            status="running",
            started_at=now,
            details=details,
        )
        self.agent_run = AgentRun.objects.create(
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            pipeline_run=self.pipeline_run,
            evidence=self.evidence,
            status="running",
            started_at=now,
            details={"cache_hit": cache_hit},
        )
        return self.pipeline_run

    def start_step(
        self,
        step_name: str,
        *,
        input_snapshot: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AgentStepLog:
        if not self.agent_run:
            raise RuntimeError("start() must be called before logging steps.")
        return AgentStepLog.objects.create(
            agent_run=self.agent_run,
            step_name=step_name,
            status="running",
            started_at=timezone.now(),
            input_snapshot=input_snapshot,
            metadata=metadata,
        )

    def complete_step(
        self,
        step: AgentStepLog,
        *,
        status: str = "completed",
        output_snapshot: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        step.status = status
        step.finished_at = timezone.now()
        if output_snapshot is not None:
            step.output_snapshot = output_snapshot
        if error:
            step.error = error
        if metadata:
            step.metadata = {**(step.metadata or {}), **metadata}
        step.save(
            update_fields=[
                "status",
                "finished_at",
                "output_snapshot",
                "error",
                "metadata",
            ]
        )

    def finish_pipeline(self, status: str, *, details: Optional[dict[str, Any]] = None) -> None:
        finished_at = timezone.now()
        if self.pipeline_run:
            self.pipeline_run.status = status
            self.pipeline_run.finished_at = finished_at
            if details:
                self.pipeline_run.details = {**(self.pipeline_run.details or {}), **details}
            self.pipeline_run.save(update_fields=["status", "finished_at", "details", "updated_at"])

        if self.agent_run:
            self.agent_run.status = status
            self.agent_run.finished_at = finished_at
            if details:
                self.agent_run.details = {**(self.agent_run.details or {}), **details}
            self.agent_run.save(update_fields=["status", "finished_at", "details", "updated_at"])

    def emit_event(self, event_type: str, payload: Optional[dict[str, Any]] = None) -> Event:
        return Event.objects.create(
            event_type=event_type,
            evidence=self.evidence,
            organization=self.evidence.organization if self.evidence else None,
            payload=payload or {},
        )
