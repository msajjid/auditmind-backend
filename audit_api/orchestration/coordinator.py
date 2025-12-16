# audit_api/orchestration/coordinator.py

from uuid import UUID

from audit_api.orchestration.workflow_engine import WorkflowEngine


class OrchestrationCoordinator:
    """
    Higher-level façade used by views / API.

    Later this can route between multiple workflows (breach analysis,
    gap detection, etc.).
    """

    def __init__(self) -> None:
        self.workflow_engine = WorkflowEngine()

    def classify_evidence(self, evidence_id: UUID | str) -> dict:
        return self.workflow_engine.run_evidence_classification(evidence_id)