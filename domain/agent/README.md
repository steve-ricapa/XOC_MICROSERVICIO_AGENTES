# Shared Agent Domain Library

Libreria de dominio compartida para agentes. Contiene contratos, esquemas y validaciones
que pueden ser usados por distintos runtimes.

## Que es
- Contratos inmutables y serializables a JSON.
- Esquemas basicos para entradas y salidas de agentes.
- Validaciones ligeras sin dependencias externas.

## Que NO hace
- No ejecuta agentes.
- No incluye runners, lifecycle ni workers.
- No se integra con Azure Functions, Flask ni servicios externos.

## Quien la usa
- Azure Functions (Agent Framework) como runtime principal.
- Backend Flask para validar o formatear payloads.
- Agentes on-prem que necesiten los mismos contratos.
