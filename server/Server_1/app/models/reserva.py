from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CarroReserva(BaseModel):
    placa: str = Field(..., description="Placa do carro")
    modelo: str = Field(..., description="Modelo do carro")
    capacidade_bateria: float = Field(..., description="Capacidade total da bateria em kWh")
    nivel_bateria_atual: float = Field(..., description="Nível atual da bateria em kWh")
    taxa_descarga: float = Field(..., description="Taxa de descarga da bateria em kWh/hora")

class ReservaRequest(BaseModel):
    request_id: str = Field(..., description="ID único da requisição")
    client_id: str = Field(..., description="ID do cliente que fez a requisição")
    server_id: str = Field(..., description="ID do servidor alvo")
    carro: CarroReserva = Field(..., description="Dados do carro")
    posto_id: int = Field(..., description="ID do posto de carregamento")

class ReservaResponse(BaseModel):
    request_id: str = Field(..., description="ID da requisição original")
    status: str = Field(..., description="Status da resposta (sucesso/erro)")
    mensagem: str = Field(..., description="Mensagem descritiva do resultado") 