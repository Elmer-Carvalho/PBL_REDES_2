from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class StationBase(BaseModel):
    """
    Modelo base para uma estação de carregamento.
    
    Attributes:
        name (str): Nome da estação de carregamento
        location (str): Localização da estação (endereço ou coordenadas)
        server_id (str): Identificador do servidor que gerencia esta estação
    """
    name: str = Field(..., description="Nome da estação de carregamento")
    location: str = Field(..., description="Localização da estação (endereço ou coordenadas)")
    server_id: str = Field(..., description="Identificador do servidor que gerencia esta estação")


class StationCreate(StationBase):
    """
    Modelo para criação de uma nova estação de carregamento.
    Herda todos os atributos de StationBase.
    """
    pass


class StationUpdate(BaseModel):
    """
    Modelo para atualização de uma estação existente.
    
    Attributes:
        name (Optional[str]): Novo nome da estação
        location (Optional[str]): Nova localização da estação
        is_available (Optional[bool]): Status de disponibilidade da estação
    """
    name: Optional[str] = Field(None, description="Novo nome da estação")
    location: Optional[str] = Field(None, description="Nova localização da estação")
    is_available: Optional[bool] = Field(None, description="Status de disponibilidade da estação")


class StationInDB(StationBase):
    """
    Modelo que representa uma estação no banco de dados.
    
    Attributes:
        id (int): Identificador único da estação
        is_available (bool): Status de disponibilidade da estação
        created_at (datetime): Data e hora de criação do registro
        updated_at (datetime): Data e hora da última atualização
    """
    id: int = Field(..., description="Identificador único da estação")
    is_available: bool = Field(..., description="Status de disponibilidade da estação")
    created_at: datetime = Field(..., description="Data e hora de criação do registro")
    updated_at: datetime = Field(..., description="Data e hora da última atualização")

    class Config:
        from_attributes = True


class StationResponse(StationInDB):
    """
    Modelo de resposta para uma estação.
    Herda todos os atributos de StationInDB.
    """
    pass


class ReservationRequest(BaseModel):
    """
    Modelo para solicitação de reserva de uma estação.
    
    Attributes:
        station_id (int): ID da estação a ser reservada
        user_name (str): Nome do usuário que está fazendo a reserva
        reservation_date (datetime): Data e hora desejada para a reserva
        server_origin (str): Identificador do servidor de origem da solicitação
    """
    station_id: int = Field(..., description="ID da estação a ser reservada")
    user_name: str = Field(..., description="Nome do usuário que está fazendo a reserva")
    reservation_date: datetime = Field(..., description="Data e hora desejada para a reserva")
    server_origin: str = Field(..., description="Identificador do servidor de origem da solicitação")


class ReservationResponse(BaseModel):
    """
    Modelo de resposta para uma solicitação de reserva.
    
    Attributes:
        success (bool): Indica se a reserva foi bem-sucedida
        message (str): Mensagem descritiva sobre o resultado da reserva
        reservation_id (Optional[str]): ID da reserva, se bem-sucedida
        station (Optional[StationResponse]): Dados da estação reservada, se bem-sucedida
    """
    success: bool = Field(..., description="Indica se a reserva foi bem-sucedida")
    message: str = Field(..., description="Mensagem descritiva sobre o resultado da reserva")
    reservation_id: Optional[str] = Field(None, description="ID da reserva, se bem-sucedida")
    station: Optional[StationResponse] = Field(None, description="Dados da estação reservada, se bem-sucedida")


class StationList(BaseModel):
    """
    Modelo para listagem de estações.
    
    Attributes:
        stations (List[StationResponse]): Lista de estações
        total (int): Total de estações na lista
    """
    stations: List[StationResponse] = Field(..., description="Lista de estações")
    total: int = Field(..., description="Total de estações na lista")
