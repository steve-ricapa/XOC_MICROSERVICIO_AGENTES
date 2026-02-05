"""Victor durable agent Azure Function (v0)."""

import json
import logging
import os
import traceback
import azure.functions as func

try:
    from agent_framework.azure import AgentFunctionApp, AzureOpenAIChatClient
except Exception as exc:
    logging.getLogger(__name__).error('Failed to import agent_framework.azure: %s', exc)
    logging.getLogger(__name__).error('Traceback: %s', traceback.format_exc())
    raise
from shared.backend_client import BackendClient
from shared.config import get_company_header_name
from shared.imports import ensure_repo_root_on_path
from shared.tools import ticket_get, ticket_patch


logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def _build_agent():
    client = AzureOpenAIChatClient(
        endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        deployment_name=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
        api_version=os.getenv('AZURE_OPENAI_API_VERSION')
    )
    return client.as_agent(
        name='VICTOR',
        instructions='You are VICTOR, a ticket execution agent.'
    )


victor_agent = _build_agent()
app = AgentFunctionApp(agents=[victor_agent])


async def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('VICTOR request received')
    try:
        company_header = get_company_header_name()
        company_id = req.headers.get(company_header)
        logger.debug('Company header name: %s', company_header)
        logger.debug('Company header present: %s', bool(company_id))
        logger.debug('Content-Type: %s', req.headers.get('Content-Type'))
        logger.debug('Query params: %s', dict(req.params or {}))

        if not company_id:
            logger.error('Missing company header: %s', company_header)
            return func.HttpResponse(
                json.dumps({'error': f'Missing {company_header} header'}),
                status_code=400,
                mimetype='application/json'
            )

        raw_body = ''
        try:
            raw_body = req.get_body().decode('utf-8', errors='replace')
            logger.debug('Raw body: %s', raw_body)
        except Exception as exc:
            logger.debug('Failed to read raw body: %s', exc)

        try:
            payload = req.get_json()
            logger.debug('Parsed JSON payload keys: %s', list(payload.keys()))
        except ValueError:
            payload = {}
            logger.debug('Request body is not JSON; defaulting to empty payload')

        ensure_repo_root_on_path()
        from domain.agent.contracts.action_plan import ActionPlan, ActionStep
        from domain.agent.contracts.agent_outputs import AgentOutput

        thread_id = req.params.get('thread_id') or payload.get('thread_id') or payload.get('threadId')
        ticket_id = payload.get('ticket_id') or payload.get('ticketId')
        message = payload.get('message') or payload.get('text') or ''
        auth_header = req.headers.get('Authorization')

        logger.info('Thread id provided: %s', bool(thread_id))
        logger.info('Ticket id provided: %s', bool(ticket_id))

        if not ticket_id:
            ticket_id = _parse_ticket_id(message)
            logger.debug('Parsed ticket id from message: %s', ticket_id)

        if not ticket_id:
            logger.error('ticket_id is required')
            return func.HttpResponse(
                json.dumps({'error': 'ticket_id is required'}),
                status_code=400,
                mimetype='application/json'
            )

        logger.info('Running agent')
        agent_result = await _run_agent(victor_agent, message or f'ticket_id={ticket_id}', thread_id)
        logger.debug('Agent result keys: %s', list(agent_result.keys()))
        resolved_thread_id = agent_result.get('thread_id') or thread_id

        backend_client = BackendClient()
        logger.info('Fetching ticket %s from backend', ticket_id)
        try:
            ticket = ticket_get(backend_client, ticket_id=int(ticket_id), company_id=company_id, auth_header=auth_header)
        except Exception as exc:
            logger.warning('Failed to fetch ticket from backend: %s', exc)
            ticket = {'id': int(ticket_id), 'subject': 'Mock Ticket', 'status': 'OPEN'}

        logger.info('Building action plan')
        action_plan = _build_action_plan(ticket, ActionPlan, ActionStep)

        patch_payload = {
            'status': 'PREAPROBADO',
            'action_plan': action_plan.to_dict()
        }
        logger.info('Patching ticket %s to PREAPROBADO', ticket_id)
        try:
            updated_ticket = ticket_patch(
                backend_client,
                ticket_id=int(ticket_id),
                company_id=company_id,
                patch=patch_payload,
                auth_header=auth_header
            )
        except Exception as exc:
            logger.warning('Failed to patch ticket in backend: %s', exc)
            updated_ticket = ticket
            updated_ticket['status'] = 'PREAPROBADO'
            updated_ticket['action_plan'] = patch_payload['action_plan']

        response_text = 'Plan generado y ticket marcado como PREAPROBADO.'

        output = AgentOutput(
            text=response_text,
            thread_id=resolved_thread_id,
            action_plan=action_plan,
            metadata={'ticket': updated_ticket}
        )

        logger.info('Returning response')
        return func.HttpResponse(
            json.dumps(output.to_dict()),
            status_code=200,
            mimetype='application/json'
        )
    except Exception as exc:
        logger.error('Unhandled exception in VICTOR function: %s', exc)
        logger.error('Traceback: %s', traceback.format_exc())
        return func.HttpResponse(
            json.dumps({
                'error': 'Internal server error',
                'message': str(exc)
            }),
            status_code=500,
            mimetype='application/json'
        )


def _parse_ticket_id(message: str) -> int | None:
    if not message:
        return None
    for token in message.replace('#', ' ').replace('=', ' ').split():
        if token.isdigit():
            return int(token)
    return None


def _build_action_plan(ticket: dict, plan_class, step_class):
    steps = (
        step_class(
            step_id='step-1',
            tool='ticket.update',
            description='Set ticket status to IN_PROGRESS',
            parameters={'status': 'IN_PROGRESS'}
        ),
        step_class(
            step_id='step-2',
            tool='ticket.note',
            description='Add operator note',
            parameters={'note': 'VICTOR v0 prepared this plan'}
        )
    )
    return plan_class(
        ticket_id=ticket.get('id'),
        summary='Mock action plan for automated remediation',
        steps=steps
    )


async def _run_agent(agent, message: str, thread_id: str | None) -> dict:
    if hasattr(agent, 'run'):
        result = await agent.run(message=message, thread_id=thread_id)
    elif hasattr(agent, 'chat'):
        result = await agent.chat(message=message, thread_id=thread_id)
    else:
        raise RuntimeError('ChatAgent does not expose a run/chat method')

    if isinstance(result, dict):
        return {
            'text': result.get('text') or result.get('message') or result.get('content'),
            'thread_id': result.get('thread_id') or result.get('threadId')
        }
    if hasattr(result, 'text'):
        return {
            'text': result.text,
            'thread_id': getattr(result, 'thread_id', thread_id)
        }
    if isinstance(result, str):
        return {'text': result, 'thread_id': thread_id}
    return {'text': str(result), 'thread_id': thread_id}
