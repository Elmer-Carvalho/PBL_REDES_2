from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import uuid
import asyncio
import logging
from app.services.mqtt_service import mqtt_service
from app.core import config
import traceback

app = FastAPI(title="Client Servidor - Interface do Cliente")

# Armazena as respostas dos servidores
responses = {}
logger = logging.getLogger(__name__)

class ReservaPayload(BaseModel):
    placa: str
    modelo: str
    capacidade_bateria: float
    nivel_bateria_atual: float
    taxa_descarga: float
    posto_id: int
    server_id: str

@app.on_event("startup")
async def startup_event():
    await mqtt_service.connect()
    await mqtt_service.subscribe(f"client/{config.MQTT_CLIENT_ID}/postos/response", on_postos_response)
    await mqtt_service.subscribe(f"client/{config.MQTT_CLIENT_ID}/postos/reserva/response", on_reserva_response)

@app.on_event("shutdown")
async def shutdown_event():
    await mqtt_service.disconnect()

async def on_postos_response(payload):
    request_id = payload.get("request_id")
    if request_id in responses:
        responses[request_id] = payload
        logger.info(f"Resposta recebida para request_id: {request_id}")

async def on_reserva_response(payload):
    request_id = payload.get("request_id")
    if request_id in responses:
        responses[request_id] = payload
        logger.info(f"Resposta de reserva recebida para request_id: {request_id}")

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

@app.post("/reservar")
async def reservar_posto(payload: ReservaPayload):
    try:
        request_id = str(uuid.uuid4())
        reserva_payload = {
            "request_id": request_id,
            "client_id": config.MQTT_CLIENT_ID,
            "server_id": payload.server_id,
            "carro": {
                "placa": payload.placa,
                "modelo": payload.modelo,
                "capacidade_bateria": payload.capacidade_bateria,
                "nivel_bateria_atual": payload.nivel_bateria_atual,
                "taxa_descarga": payload.taxa_descarga
            },
            "posto_id": payload.posto_id
        }
        responses[request_id] = None
        await mqtt_service.publish("server/postos/reserva", reserva_payload)
        # Aguarda resposta por até 10 segundos
        for _ in range(100):
            if responses[request_id] is not None:
                response = responses.pop(request_id)
                return response
            await asyncio.sleep(0.1)
        responses.pop(request_id)
        raise HTTPException(status_code=504, detail="Timeout: Sem resposta do servidor para reserva")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao reservar posto: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erro ao reservar posto: {str(e)}") 