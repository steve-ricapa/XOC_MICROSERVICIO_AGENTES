"""Agent output contract.

Defines a minimal, JSON-serializable payload for agent responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .action_plan import ActionPlan, _validate_json_value


@dataclass(frozen=True)
class AgentOutput:
    """Immutable output payload for an agent."""

    text: str
    thread_id: str | None = None
    action_plan: ActionPlan | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError('text must be a non-empty string')
        if self.thread_id is not None and not isinstance(self.thread_id, str):
            raise ValueError('thread_id must be a string when provided')
        if self.action_plan is not None and not isinstance(self.action_plan, ActionPlan):
            raise ValueError('action_plan must be an ActionPlan when provided')
        _validate_json_value(self.metadata, 'metadata')

    def to_dict(self) -> dict:
        return {
            'text': self.text,
            'thread_id': self.thread_id,
            'action_plan': self.action_plan.to_dict() if self.action_plan else None,
            'metadata': self.metadata
        }
