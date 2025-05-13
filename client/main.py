"""
Aplicação principal do sistema de reserva de postos de carregamento.

Este módulo configura e inicializa a aplicação FastAPI, incluindo:
- Configuração do CORS
- Registro dos routers
- Configuração da documentação Swagger
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    API para gerenciamento de reservas de postos de carregamento.
    
    Esta API permite:
    - Consultar postos de carregamento disponíveis
    - Realizar reservas em postos específicos
    - Gerenciar a comunicação entre diferentes servidores
    
    A API utiliza MQTT para comunicação entre servidores e suporta
    operações distribuídas para garantir a consistência das reservas.
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar as origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Habilita o reload automático em desenvolvimento
    )
