import json
from pathlib import Path
from django.conf import settings

class EvidenceStorageService:
    """
    Writes evidence payload to local filesystem (dev) and returns a URI like:
    local://uploads/<org>/<evidence>/raw.json
    """

    def write_raw_payload(
        self,
        organization_id,
        evidence_id,
        *,
        raw_text: str | None,
        raw_json: dict | list | None,
    ) -> tuple[str, int]:
        base_dir: Path = settings.EVIDENCE_UPLOAD_DIR
        target_dir = base_dir / str(organization_id) / str(evidence_id)
        target_dir.mkdir(parents=True, exist_ok=True)

        if raw_json is not None:
            filename = "raw.json"
            content = json.dumps(raw_json, ensure_ascii=False, indent=2)
        else:
            filename = "raw.txt"
            content = raw_text or ""

        file_path = target_dir / filename
        file_path.write_text(content, encoding="utf-8")

        # URI stored in DB (future-proof)
        uri = f"local://uploads/{organization_id}/{evidence_id}/{filename}"
        size = len(content.encode("utf-8"))
        return uri, size