"""Shared configuration for Azure Functions agents."""

import os


def get_backend_url() -> str:
    return os.getenv('BACKEND_URL', 'http://localhost:5000/api').rstrip('/')


def get_backend_timeout() -> int:
    value = os.getenv('BACKEND_TIMEOUT_SECONDS', '10')
    try:
        return int(value)
    except ValueError:
        return 10


def get_company_header_name() -> str:
    return os.getenv('XCOMPANY_HEADER', 'X-Company-Id')
