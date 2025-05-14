from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date
import paho.mqtt.client as mqtt
import json
import uvicorn
from typing import List, Optional

app = FastAPI(title="Servidor 3 - Rede de Postos de Recarga")

# Modelos
class Posto(BaseModel):
    id: str
    nome: str
    cidade: str
    estado: str
    status: str = "LIVRE"  # LIVRE, RESERVADO, EM_USO

class Reserva(BaseModel):
    id_posto: str
    data: date
    id_carro: str
    servidor_origem: str

# Dados em memória
postos = [
    Posto(
        id="RS001",
        nome="Posto Porto Alegre",
        cidade="Porto Alegre",
        estado="RS"
    ),
    Posto(
        id="RS002",
        nome="Posto Caxias do Sul",
        cidade="Caxias do Sul",
        estado="RS"
    )
]

reservas = []

# Configuração MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPICS = ["reservas/#", "atualizacoes/#"]
SERVIDOR_ID = "servidor3"

# Cliente MQTT
mqtt_client = mqtt.Client(f"servidor3_{id}")

def on_connect(client, userdata, flags, rc):
    print(f"Conectado ao broker MQTT com código: {rc}")
    for topic in MQTT_TOPICS:
        client.subscribe(topic)

def on_message(client, userdata, msg):
    try:
        dados = json.loads(msg.payload.decode())
        if msg.topic.startswith("reservas/solicitar"):
            processar_solicitacao_reserva(dados)
        elif msg.topic.startswith("reservas/confirmar"):
            processar_confirmacao_reserva(dados)
        elif msg.topic.startswith("atualizacoes/posto"):
            atualizar_status_posto(dados)
    except Exception as e:
        print(f"Erro ao processar mensagem MQTT: {e}")

def broadcast_mensagem(topico: str, mensagem: dict):
    mqtt_client.publish(topico, json.dumps(mensagem))

# Configurando callbacks MQTT
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Endpoints da API
@app.get("/postos", response_model=List[Posto])
async def listar_postos():
    return postos

@app.get("/postos/{posto_id}")
async def obter_posto(posto_id: str):
    for posto in postos:
        if posto.id == posto_id:
            return posto
    raise HTTPException(status_code=404, detail="Posto não encontrado")

@app.post("/reservas")
async def criar_reserva(reserva: Reserva):
    # Verifica se o posto existe
    posto = next((p for p in postos if p.id == reserva.id_posto), None)
    if not posto:
        # Se não encontrou o posto localmente, faz broadcast da solicitação
        broadcast_mensagem("reservas/solicitar", reserva.dict())
        return {"message": "Solicitação de reserva enviada para outros servidores"}
    
    # Se encontrou o posto localmente, verifica disponibilidade
    if posto.status != "LIVRE":
        raise HTTPException(status_code=400, detail="Posto não está disponível")
    
    # Verifica se já existe reserva para esta data
    if any(r.id_posto == reserva.id_posto and r.data == reserva.data for r in reservas):
        raise HTTPException(status_code=400, detail="Já existe reserva para esta data")
    
    # Cria a reserva
    reservas.append(reserva)
    posto.status = "RESERVADO"
    
    # Notifica outros servidores
    broadcast_mensagem("reservas/confirmar", {
        "id_posto": posto.id,
        "status": "RESERVADO",
        "data": reserva.data.isoformat(),
        "id_carro": reserva.id_carro
    })
    
    return {"message": "Reserva realizada com sucesso"}

@app.put("/postos/{posto_id}/status")
async def atualizar_posto(posto_id: str, status: str):
    posto = next((p for p in postos if p.id == posto_id), None)
    if not posto:
        raise HTTPException(status_code=404, detail="Posto não encontrado")
    
    posto.status = status
    broadcast_mensagem("atualizacoes/posto", {
        "id_posto": posto_id,
        "status": status
    })
    
    return {"message": "Status atualizado com sucesso"}

# Funções auxiliares
def processar_solicitacao_reserva(dados: dict):
    # Processa solicitação de reserva recebida de outro servidor
    pass

def processar_confirmacao_reserva(dados: dict):
    # Atualiza o status local com base na confirmação de reserva
    pass

def atualizar_status_posto(dados: dict):
    # Atualiza o status de um posto com base na mensagem recebida
    pass

# Inicialização
@app.on_event("startup")
async def startup_event():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Erro ao conectar ao broker MQTT: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)