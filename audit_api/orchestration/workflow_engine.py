# audit_api/orchestration/workflow_engine.py

from uuid import UUID

from django.shortcuts import get_object_or_404

from audit_api.models import Evidence
from audit_api.agents.evidence_classifier import EvidenceClassifierAgent


class WorkflowEngine:
    """
    Coordinates end-to-end workflows.

    For now we only have 'evidence_classification', but this can grow to
    support different pipelines later.
    """

    def run_evidence_classification(self, evidence_id: UUID | str) -> dict:
        evidence = get_object_or_404(Evidence, pk=evidence_id)
        agent = EvidenceClassifierAgent()
        return agent.classify(evidence)