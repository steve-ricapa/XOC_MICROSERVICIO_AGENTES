"""Minimal tools that always go through BackendClient."""

from shared.backend_client import BackendClient


def ticket_create(client: BackendClient, subject: str, description: str, company_id: str, status: str | None, auth_header: str | None) -> dict:
    return client.ticket_create(company_id=company_id, subject=subject, description=description, status=status, auth_header=auth_header)


def ticket_get(client: BackendClient, ticket_id: int, company_id: str, auth_header: str | None) -> dict:
    return client.ticket_get(company_id=company_id, ticket_id=ticket_id, auth_header=auth_header)


def ticket_patch(client: BackendClient, ticket_id: int, company_id: str, patch: dict, auth_header: str | None) -> dict:
    return client.ticket_patch(company_id=company_id, ticket_id=ticket_id, patch=patch, auth_header=auth_header)
