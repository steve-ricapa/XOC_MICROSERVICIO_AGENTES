"""Shared configuration for Azure Functions agents."""

import os


def get_backend_url() -> str:
    backend_url = os.getenv('BACKEND_URL')
    if not backend_url:
        raise ValueError('BACKEND_URL is required')
    return backend_url.rstrip('/')


def get_backend_timeout() -> int:
    value = os.getenv('BACKEND_TIMEOUT_SECONDS', '10')
    try:
        return int(value)
    except ValueError:
        return 10


def get_company_header_name() -> str:
    return os.getenv('XCOMPANY_HEADER', 'X-Company-Id')


def get_agent_access_key() -> str | None:
    return os.getenv('AGENT_ACCESS_KEY')


def get_agent_type(default_type: str) -> str:
    return os.getenv('AGENT_TYPE', default_type)
