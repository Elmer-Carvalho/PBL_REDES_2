from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import logging
from datetime import datetime
import csv
import os

from .database import engine, Base, get_db
from .config import get_settings
from .mqtt.client import mqtt_client
from .mqtt.handlers import register_handlers
from .models.ponto_carregamento import PontoCarregamento

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
    title="Servidor 2 de Carregamento de Veículos Elétricos",
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
    """Inicializa o cliente MQTT e registra os handlers"""
    try:
        register_handlers()
        await mqtt_client.start()
        logger.info("Servidor 2 iniciado com sucesso")
        # Importa pontos de carregamento do CSV se necessário
        db = next(get_db())
        if db.query(PontoCarregamento).count() == 0:
            csv_path = os.path.join(os.path.dirname(__file__), "pontos_carregamento.csv")
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                pontos = []
                for row in reader:
                    ponto = PontoCarregamento(
                        nome=row["nome"],
                        localizacao=f"{row['latitude']},{row['longitude']}",
                        potencia_maxima=22.0,  # valor fictício padrão
                        tipo_conector="CCS",  # valor fictício padrão
                        disponivel=(row["status"].lower() == "ativo"),
                        em_manutencao=False,
                        preco_kwh=2.5  # valor fictício padrão
                    )
                    pontos.append(ponto)
                db.add_all(pontos)
                db.commit()
            logger.info(f"{len(pontos)} pontos de carregamento importados do CSV.")
        else:
            logger.info("Pontos de carregamento já existentes no banco de dados.")
    except Exception as e:
        logger.error(f"Erro ao iniciar o servidor: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Para o cliente MQTT ao encerrar o servidor"""
    try:
        await mqtt_client.stop()
        logger.info("Servidor 2 encerrado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao encerrar o servidor: {str(e)}")

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