from fastapi import FastAPI, Query
import uuid
import threading
import time
import logging

from app.services.mqtt_service import mqtt_service
from app.core import config

app = FastAPI(title="Client Servidor - Interface do Cliente")

# Armazena a última resposta recebida dos servidores
last_response = {}

logger = logging.getLogger(__name__)

@app.on_event("startup")
def startup_event():
    mqtt_service.connect()
    # Inscreve-se no tópico de resposta dos servidores
    mqtt_service.subscribe(f"client/{config.MQTT_CLIENT_ID}/postos/response", on_postos_response)

def on_postos_response(payload):
    global last_response
    logger.info(f"Recebida resposta dos postos: {payload}")
    if "request_id" in payload and "postos" in payload:
        last_response[payload["request_id"]] = payload["postos"]
    else:
        logger.error(f"Payload inválido recebido: {payload}")

@app.get("/postos")
def get_postos(server_id: str = Query(..., description="ID do servidor desejado")):
    # Gera um request_id único para correlacionar respostas
    request_id = str(uuid.uuid4())
    logger.info(f"Solicitando postos do servidor {server_id} com request_id {request_id}")
    
    # Publica solicitação para os servidores
    mqtt_service.publish(
        "server/postos/request",
        {
            "request_id": request_id,
            "client_id": config.MQTT_CLIENT_ID,
            "server_id": server_id
        }
    )
    
    # Aguarda resposta
    timeout = 5
    for _ in range(timeout * 10):
        if request_id in last_response:
            postos = last_response.pop(request_id)
            logger.info(f"Retornando {len(postos)} postos para o cliente")
            return {"postos": postos}
        time.sleep(0.1)
    
    logger.error(f"Timeout aguardando resposta do servidor {server_id}")
    return {"erro": "Sem resposta do servidor solicitado"} 