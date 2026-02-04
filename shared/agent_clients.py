"""Local chat client for Agent Framework integration."""

from typing import Any


class RuleBasedChatClient:
    """Deterministic chat client for local durable agents."""

    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name

    def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict:
        last_message = _last_user_message(messages)
        if self.agent_name.upper() == 'SOPHIA':
            classification = _classify_message(last_message)
            text = _build_sophia_text(classification)
        else:
            text = 'VICTOR listo para generar un plan de accion.'
        return {'content': text}


def _last_user_message(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get('role') == 'user':
            return str(message.get('content') or '')
    return ''


def _classify_message(message: str) -> str:
    normalized = (message or '').lower()
    keywords = ('automated', 'auto', 'runbook', 'playbook', 'block', 'isolate', 'disable', 'quarantine')
    if any(keyword in normalized for keyword in keywords):
        return 'AUTOMATED'
    return 'MANUAL'


def _build_sophia_text(classification: str) -> str:
    if classification == 'AUTOMATED':
        return 'Caso clasificado como AUTOMATED. Creando ticket para aprobacion.'
    return 'Caso clasificado como MANUAL. Se requiere revision humana.'
