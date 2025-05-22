from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CarroReserva(BaseModel):
    placa: str
    modelo: str
    capacidade_bateria: float
    nivel_bateria_atual: float
    taxa_descarga: float

class ReservaRequest(BaseModel):
    request_id: str
    client_id: str
    server_id: str
    carro: CarroReserva
    posto_id: int

class ReservaResponse(BaseModel):
    request_id: str
    status: str
    mensagem: str 