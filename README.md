# Agent Functions (Azure Functions)

This folder hosts Azure Functions endpoints for durable SOPHIA and VICTOR agents.
The backend remains authoritative and is accessed only via HTTP.

## Structure
- `sophia_agent/`: HTTP-triggered durable SOPHIA endpoint.
- `victor_agent/`: HTTP-triggered durable VICTOR endpoint.
- `shared/`: Backend client, tools, and configuration helpers.

## Durable memory model
- Thread state is managed by Azure Functions + Durable Task Scheduler (DTS).
- The framework creates/continues threads automatically.
- Pass `thread_id` as a query parameter to continue a conversation.
- The response always includes the `thread_id` assigned by the runtime.
 - Thread history can be inspected in the local DTS dashboard.

## Local development
1) Start the DTS emulator (Durable Task Scheduler) in Docker and keep it running:
```
docker run --rm -p 8080:8080 -p 8082:8082 ghcr.io/microsoft/dts-emulator:latest
```

2) Configure local settings:
```
cp local.settings.json.example local.settings.json
```

3) Start Azure Functions locally:
```
func start
```

## Example requests

### Start a new SOPHIA conversation (no thread_id)
```
curl -X POST http://localhost:7071/api/agents/SophiaDurableAgent/run \
  -H "Content-Type: application/json" \
  -H "X-Company-Id: 42" \
  -d '{"message": "Detectamos una vulnerabilidad critica, bloquear automaticamente"}'
```

### Continue SOPHIA conversation (with thread_id)
```
curl -X POST "http://localhost:7071/api/agents/SophiaDurableAgent/run?thread_id=<thread_id>" \
  -H "Content-Type: application/json" \
  -H "X-Company-Id: 42" \
  -d '{"message": "Continua con el analisis"}'
```

### Run VICTOR for a ticket
```
curl -X POST http://localhost:7071/api/agents/VictorDurableAgent/run \
  -H "Content-Type: application/json" \
  -H "X-Company-Id: 42" \
  -d '{"ticket_id": 1234}'
```

### Continue VICTOR conversation (with thread_id)
```
curl -X POST "http://localhost:7071/api/agents/VictorDurableAgent/run?thread_id=<thread_id>" \
  -H "Content-Type: application/json" \
  -H "X-Company-Id: 42" \
  -d '{"ticket_id": 1234, "message": "Sigue con el plan"}'
```

## Notes
- Thread persistence is handled by the Azure Functions durable task extension.
- No manual thread storage is used in code.
