"""Sophia durable agent Azure Function (v0)."""

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
from shared.tools import ticket_create


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
        name='SOPHIA',
        instructions='Eres SOPHIA, una agente de triage muy amable. DEBES responder SIEMPRE en ESPAÑOL. Comienza siempre tu respuesta con un saludo afectuoso y preséntate brevemente.'
    )


sophia_agent = _build_agent()
app = AgentFunctionApp(agents=[sophia_agent])


async def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('SOPHIA request received')
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
        from domain.agent.contracts.agent_outputs import AgentOutput

        message = payload.get('message') or payload.get('text') or ''
        thread_id = req.params.get('thread_id') or payload.get('thread_id') or payload.get('threadId')
        auth_header = req.headers.get('Authorization')

        logger.info('Message length: %s', len(message))
        logger.info('Thread id provided: %s', bool(thread_id))

        logger.info('Running agent')
        agent_result = await _run_agent(sophia_agent, message, thread_id)
        logger.debug('Agent result keys: %s', list(agent_result.keys()))

        classification = _classify_message(message)
        response_text = agent_result.get('text') or _build_response_text(classification)
        resolved_thread_id = agent_result.get('thread_id') or thread_id
        metadata: dict[str, object] = {'classification': classification}

        backend_client = BackendClient()
        ticket_response = None
        if classification == 'AUTOMATED':
            subject = 'Automated security request'
            description = message or 'Automated request captured by SOPHIA'
            logger.info('Creating ticket in backend')
            try:
                ticket_response = ticket_create(
                    backend_client,
                    subject=subject,
                    description=description,
                    company_id=company_id,
                    auth_header=auth_header
                )
            except Exception as exc:
                logger.warning('Failed to create ticket in backend (server might be down): %s', exc)
                ticket_response = {
                    'id': 0,
                    'subject': subject,
                    'status': 'MOCK_CREATED',
                    'message': 'Backend unavailable, using mock response'
                }
            metadata['ticket'] = ticket_response

        output = AgentOutput(
            text=response_text,
            thread_id=resolved_thread_id,
            metadata=metadata
        )

        logger.info('Returning response')
        return func.HttpResponse(
            json.dumps(output.to_dict()),
            status_code=200,
            mimetype='application/json'
        )
    except Exception as exc:
        logger.error('Unhandled exception in SOPHIA function: %s', exc)
        logger.error('Traceback: %s', traceback.format_exc())
        return func.HttpResponse(
            json.dumps({
                'error': 'Internal server error',
                'message': str(exc)
            }),
            status_code=500,
            mimetype='application/json'
        )


def _classify_message(message: str) -> str:
    normalized = (message or '').lower()
    keywords = ('automated', 'auto', 'runbook', 'playbook', 'block', 'isolate', 'disable', 'quarantine')
    if any(keyword in normalized for keyword in keywords):
        return 'AUTOMATED'
    return 'MANUAL'


def _build_response_text(classification: str) -> str:
    if classification == 'AUTOMATED':
        return 'Caso clasificado como AUTOMATED. Creando ticket para aprobacion.'
    return 'Caso clasificado como MANUAL. Se requiere revision humana.'


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
