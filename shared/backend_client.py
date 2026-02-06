"""HTTP client for backend access."""

from typing import Any, Optional
import requests

from shared import config


class BackendClient:
    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None) -> None:
        self.base_url = (base_url or config.get_backend_url()).rstrip('/')
        self.timeout = timeout if timeout is not None else config.get_backend_timeout()

    def ticket_create(self, company_id: str, subject: str, description: str, status: Optional[str] = None, auth_header: Optional[str] = None) -> dict:
        payload = {
            'subject': subject,
            'description': description
        }
        if status:
            payload['status'] = status
        return self._request(
            'post',
            '/tickets/agent-create',
            company_id=company_id,
            json=payload,
            auth_header=auth_header
        )

    def ticket_get(self, company_id: str, ticket_id: int, auth_header: Optional[str] = None) -> dict:
        return self._request(
            'get',
            f'/tickets/{ticket_id}',
            company_id=company_id,
            auth_header=auth_header
        )

    def ticket_patch(self, company_id: str, ticket_id: int, patch: dict, auth_header: Optional[str] = None) -> dict:
        return self._request(
            'put',
            f'/tickets/{ticket_id}',
            company_id=company_id,
            json=patch,
            auth_header=auth_header
        )

    def _request(
        self,
        method: str,
        path: str,
        company_id: str,
        json: Optional[dict] = None,
        auth_header: Optional[str] = None
    ) -> dict:
        url = f'{self.base_url}{path}'
        headers: dict[str, Any] = {
            config.get_company_header_name(): str(company_id)
        }
        if auth_header:
            headers['Authorization'] = auth_header

        response = requests.request(
            method=method,
            url=url,
            json=json,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
