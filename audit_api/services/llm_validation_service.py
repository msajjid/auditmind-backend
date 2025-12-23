from typing import Iterable, Tuple


class LLMValidationService:
    """
    Placeholder LLM validation stage.

    Keeps confidence as-is but captures a justification string so the
    pipeline surface area is wired for future LLM calls.
    """

    def validate(
        self,
        *,
        text: str,
        control_references: Iterable[str],
        confidence: float,
    ) -> Tuple[float, str]:
        justification = "LLM validation stub: no adjustment applied."
        return confidence, justification
