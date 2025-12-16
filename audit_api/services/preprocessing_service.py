import json

class EvidencePreprocessingService:
    def extract_text(self, *, raw_text: str | None, raw_json: object | None) -> str:
        # For now, deterministic:
        # - if JSON: pretty string
        # - else: raw_text
        if raw_json is not None:
            return json.dumps(raw_json, ensure_ascii=False, indent=2)
        return (raw_text or "").strip()
    



import hashlib
import json
from typing import Any


class EvidencePreprocessingService:
    """Deterministic text extraction + hashing for Evidence."""

    MAX_LEN = 200_000  # safety cap to avoid storing megabytes in a single row

    def extract_text(self, *, raw_text: str | None, raw_json: object | None) -> str:
        if raw_json is not None:
            obj: Any = raw_json

            # If someone passed JSON as a string, try to parse it.
            if isinstance(raw_json, str):
                s = raw_json.strip()
                if s:
                    try:
                        obj = json.loads(s)
                    except Exception:
                        # Not valid JSON; store the string as-is.
                        return self._cap(s)

            try:
                text = json.dumps(
                    obj,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                    default=str,  # UUID/Decimal/etc.
                )
            except Exception:
                text = str(obj)

            text = (text or "").strip()

            if text in {"{", "["}:
                text = str(obj).strip()

            return self._cap(text)

        return self._cap((raw_text or "").strip())

    def content_hash(self, text: str) -> str:
        """Stable hash used to reuse classifications for identical payloads."""
        return hashlib.sha256((text or "").strip().encode("utf-8")).hexdigest()

    def _cap(self, text: str) -> str:
        if len(text) > self.MAX_LEN:
            return text[: self.MAX_LEN]
        return text
