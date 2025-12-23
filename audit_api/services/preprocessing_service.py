import hashlib
import json
import mimetypes
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

    def extract_text_from_file(self, *, filename: str, data: bytes) -> str:
        """Best-effort extraction for uploaded files (text/json)."""
        name = (filename or "").lower()
        mime, _ = mimetypes.guess_type(name)

        # Try JSON first if hinted by extension or MIME type.
        if name.endswith(".json") or (mime and mime == "application/json"):
            try:
                decoded = data.decode("utf-8", errors="ignore")
                parsed = json.loads(decoded)
                return self.extract_text(raw_text=None, raw_json=parsed)
            except Exception:
                pass

        # Text-like files: decode and trim.
        if name.endswith((".txt", ".md", ".log", ".csv")) or (mime and mime.startswith("text/")):
            return self._cap(data.decode("utf-8", errors="ignore").strip())

        # Fallback: attempt utf-8 then latin-1 decode.
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1", errors="ignore")

        return self._cap(text.strip())

    def content_hash(self, text: str) -> str:
        """Stable hash used to reuse classifications for identical payloads."""
        return hashlib.sha256((text or "").strip().encode("utf-8")).hexdigest()

    def _cap(self, text: str) -> str:
        if len(text) > self.MAX_LEN:
            return text[: self.MAX_LEN]
        return text
