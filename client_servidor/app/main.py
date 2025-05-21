from fastapi import FastAPI, Query
import uuid
import asyncio
import logging
from app.services.mqtt_service import mqtt_service
from app.core import config

app = FastAPI(title="Client Servidor - Interface do Cliente")

# Armazena a última resposta recebida dos servidores
last_response = {}

logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await mqtt_service.connect()
    # Inscreve-se no tópico de resposta dos servidores
    await mqtt_service.subscribe(f"client/{config.MQTT_CLIENT_ID}/postos/response", on_postos_response)

@app.on_event("shutdown")
async def shutdown_event():
    await mqtt_service.disconnect()

async def on_postos_response(payload):
    logger.info(f"[HANDLER] Recebido request_id: {payload.get('request_id')}")
    logger.info(f"[HANDLER] Payload recebido: {payload}")
    request_id = payload.get("request_id")
    logger.info(f"[HANDLER] last_response.keys() antes: {list(last_response.keys())}")
    if request_id in last_response:
        last_response[request_id] = payload
        logger.info(f"[HANDLER] Atualizado last_response para {request_id}")
    else:
        logger.warning(f"[HANDLER] request_id {request_id} não está em last_response")
    logger.info(f"[HANDLER] last_response.keys() depois: {list(last_response.keys())}")

@app.get("/postos")
async def get_postos(server_id: str = Query(..., description="ID do servidor a ser consultado")):
    try:
        request_id = str(uuid.uuid4())
        request_payload = {
            "request_id": request_id,
            "client_id": config.MQTT_CLIENT_ID,
            "server_id": server_id
        }
        last_response[request_id] = None
        await mqtt_service.publish("server/postos/request", request_payload)
        logger.info(f"[POSTOS] Requisição enviada para o servidor {server_id} com request_id {request_id}")
        logger.info(f"[POSTOS] last_response.keys() após envio: {list(last_response.keys())}")
        for _ in range(100):  # 100 tentativas de 100ms = 10 segundos
            if last_response[request_id] is not None:
                response = last_response.pop(request_id)
                logger.info(f"[POSTOS] Resposta recebida: {response}")
                return response
            await asyncio.sleep(0.1)
        logger.warning(f"Timeout aguardando resposta do servidor {server_id} para request_id {request_id}")
        return {"erro": "Sem resposta do servidor solicitado"}
    except Exception as e:
        logger.error(f"Erro ao consultar postos: {str(e)}")
        return {"erro": f"Erro ao consultar postos: {str(e)}"} 