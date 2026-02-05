import azure.functions as func
import logging
import os
import sys

# Asegurar que la raíz esté en el path para los imports de 'shared' y 'domain'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importar las lógicas de los agentes
from sophia_agent import main as sophia_main
from victor_agent import main as victor_main

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="agents/SophiaDurableAgent/run", methods=["POST"])
async def sophia_agent_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Trigger de SOPHIA ejecutado desde function_app.py')
    return await sophia_main(req)

@app.route(route="agents/VictorDurableAgent/run", methods=["POST"])
async def victor_agent_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Trigger de VICTOR ejecutado desde function_app.py')
    return await victor_main(req)
