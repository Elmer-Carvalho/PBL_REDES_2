from fastapi import FastAPI, Query
import uuid
import asyncio
import logging
from app.services.mqtt_service import mqtt_service
from app.core import config

app = FastAPI(title="Client Servidor - Interface do Cliente")

# Armazena as respostas dos servidores
responses = {}
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await mqtt_service.connect()
    await mqtt_service.subscribe(f"client/{config.MQTT_CLIENT_ID}/postos/response", on_postos_response)

@app.on_event("shutdown")
async def shutdown_event():
    await mqtt_service.disconnect()

async def on_postos_response(payload):
    request_id = payload.get("request_id")
    if request_id in responses:
        responses[request_id] = payload
        logger.info(f"Resposta recebida para request_id: {request_id}")

@app.get("/postos")
async def get_postos(server_id: str = Query(..., description="ID do servidor a ser consultado")):
    try:
        request_id = str(uuid.uuid4())
        request_payload = {
            "request_id": request_id,
            "client_id": config.MQTT_CLIENT_ID,
            "server_id": server_id
        }
        
        responses[request_id] = None
        await mqtt_service.publish("server/postos/request", request_payload)
        
        # Aguarda resposta por até 5 segundos
        for _ in range(50):
            if responses[request_id] is not None:
                response = responses.pop(request_id)
                return response
            await asyncio.sleep(0.1)
            
        responses.pop(request_id)
        return {"erro": "Timeout: Sem resposta do servidor solicitado"}
        
    except Exception as e:
        logger.error(f"Erro ao consultar postos: {str(e)}")
        return {"erro": f"Erro ao consultar postos: {str(e)}"} 