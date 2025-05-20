from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import logging
from datetime import datetime

from .database import engine, Base, get_db
from .config import get_settings
from .mqtt.client import mqtt_client
from .mqtt.handlers import register_handlers

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cria as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

# Configurações
settings = get_settings()

# Cria a aplicação FastAPI
app = FastAPI(
    title="Servidor de Carregamento de Veículos Elétricos",
    description="API para gerenciamento de pontos de carregamento e reservas",
    version="1.0.0"
)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique as origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Eventos de inicialização e encerramento
@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando o servidor...")
    # Inicia o cliente MQTT
    mqtt_client.start()
    # Registra os handlers MQTT
    register_handlers()
    logger.info("Servidor iniciado com sucesso!")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Encerrando o servidor...")
    # Para o cliente MQTT
    mqtt_client.stop()
    logger.info("Servidor encerrado com sucesso!")

# Rotas básicas
@app.get("/")
async def root():
    return {
        "mensagem": "Bem-vindo ao Servidor de Carregamento de Veículos Elétricos",
        "servidor": settings.SERVER_ID,
        "status": "online",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def verificar_status():
    return {
        "servidor": settings.SERVER_ID,
        "status": "online",
        "mqtt_conectado": mqtt_client.connected,
        "timestamp": datetime.now().isoformat()
    }

# Importa e inclui os routers
from .routers import carros, pontos, reservas

app.include_router(carros.router, prefix="/carros", tags=["carros"])
app.include_router(pontos.router, prefix="/pontos", tags=["pontos"])
app.include_router(reservas.router, prefix="/reservas", tags=["reservas"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENVIRONMENT == "development"
    ) 