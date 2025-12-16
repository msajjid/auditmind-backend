# audit_api/services/evidence_service.py

from typing import Iterable, Optional
from uuid import UUID

from audit_api.models import Evidence, Organization
from audit_api.services.storage_service import EvidenceStorageService
from audit_api.services.preprocessing_service import EvidencePreprocessingService


class EvidenceService:
    """
    Django ORM-based Evidence service.

    This replaces the old SQLAlchemy-based EvidenceService.
    """

    def __init__(self):
        self.storage = EvidenceStorageService()
        self.preprocessing = EvidencePreprocessingService()

    def create_from_payload(self, payload: dict) -> Evidence:
        org = Organization.objects.get(id=payload["organization_id"])

        def derive_title() -> str:
            if payload.get("title"):
                return payload["title"]
            if payload.get("raw_text"):
                snippet = payload["raw_text"][:60].strip().replace("\n", " ")
                return snippet or "Untitled evidence"
            if payload.get("raw_json") is not None:
                return "JSON evidence"
            return "Untitled evidence"

        evidence = Evidence.objects.create(
            organization=org,
            uploaded_by_id=payload.get("uploaded_by"),
            title=derive_title(),
            description=payload.get("description"),
            evidence_type_id=payload.get("evidence_type_id"),
            source_type_id=payload.get("source_type_id"),
            status="uploaded",
        )

        storage_uri, computed_size = self.storage.write_raw_payload(
            org.id,
            evidence.id,
            raw_text=payload.get("raw_text"),
            raw_json=payload.get("raw_json"),
        )

        evidence.storage_path = storage_uri
        evidence.file_size = payload.get("file_size") or computed_size

        evidence.extracted_text = self.preprocessing.extract_text(
            raw_text=payload.get("raw_text"),
            raw_json=payload.get("raw_json"),
        )

        evidence.save(update_fields=["storage_path", "file_size", "extracted_text"])
        return evidence

    def list_by_org(self, organization_id: UUID) -> Iterable[Evidence]:
        return (
            Evidence.objects
            .filter(organization_id=organization_id)
            .order_by("-created_at")
        )

    def get(self, evidence_id: UUID) -> Evidence:
        return Evidence.objects.get(pk=evidence_id)

    def create(
        self,
        *,
        organization_id: UUID,
        uploaded_by: Optional[UUID],
        title: str,
        description: Optional[str],
        storage_path: str,
        evidence_type_id: Optional[str],
        source_type_id: Optional[str],
        file_size: Optional[int],
    ) -> Evidence:
        evidence = Evidence.objects.create(
            organization_id=organization_id,
            uploaded_by_id=uploaded_by,
            title=title,
            description=description,
            storage_path=storage_path,
            evidence_type_id=evidence_type_id,
            source_type_id=source_type_id,
            file_size=file_size,
            status="uploaded",
        )
        return evidence
