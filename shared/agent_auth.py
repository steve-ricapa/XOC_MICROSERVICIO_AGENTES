"""Agent authentication helper."""

from __future__ import annotations

import time
from typing import Optional

import requests

from shared import config


_cached_token: Optional[str] = None
_token_expires_at: float = 0.0


def get_agent_token(company_id: str, agent_type: str) -> str:
    global _cached_token, _token_expires_at

    if _cached_token and time.time() < _token_expires_at:
        return _cached_token

    access_key = config.get_agent_access_key()
    if not access_key:
        raise ValueError('AGENT_ACCESS_KEY is required for agent authentication')

    payload = {
        'companyId': company_id,
        'agentType': agent_type,
        'agentAccessKey': access_key
    }

    url = f"{config.get_backend_url()}/agents/auth/token"
    last_error: Exception | None = None
    data: dict | None = None
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, timeout=config.get_backend_timeout())
            response.raise_for_status()
            data = response.json()
            last_error = None
            break
        except Exception as exc:
            last_error = exc
            time.sleep(0.5 * (2 ** attempt))

    if last_error:
        raise last_error

    if not data:
        raise ValueError('Backend did not return token payload')

    token = data.get('access_token')
    if not token:
        raise ValueError('Backend did not return access_token')

    expires_in = data.get('expires_in', 3600)
    _cached_token = token
    _token_expires_at = time.time() + max(int(expires_in) - 30, 0)
    return token
