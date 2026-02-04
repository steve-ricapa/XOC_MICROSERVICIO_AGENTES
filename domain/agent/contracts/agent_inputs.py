"""Agent input contract.

Defines a minimal, JSON-serializable payload for agent requests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .action_plan import _validate_json_value


@dataclass(frozen=True)
class AgentInput:
    """Immutable input payload for an agent."""

    message: str | None = None
    ticket_id: int | None = None
    thread_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.ticket_id is not None and not isinstance(self.ticket_id, int):
            raise ValueError('ticket_id must be an integer when provided')
        if self.thread_id is not None and not isinstance(self.thread_id, str):
            raise ValueError('thread_id must be a string when provided')
        if self.message is not None and not isinstance(self.message, str):
            raise ValueError('message must be a string when provided')
        _validate_json_value(self.metadata, 'metadata')

    def to_dict(self) -> dict:
        return {
            'message': self.message,
            'ticket_id': self.ticket_id,
            'thread_id': self.thread_id,
            'metadata': self.metadata
        }
