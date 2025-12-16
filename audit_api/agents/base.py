# audit_api/agents/base.py

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AgentContext:
    """Placeholder for future shared context (org, user, request, etc.)."""
    metadata: Dict[str, Any] | None = None


class BaseAgent:
    name: str = "base-agent"
    version: str = "0.0.1"

    def __init__(self, context: Optional[AgentContext] = None) -> None:
        self.context = context or AgentContext()