from fastapi import APIRouter, HTTPException
import logging

from client.app.schemas.station import (
    ReservationRequest,
    ReservationResponse,
    StationList
)
from client.app.services.server_communication import server_communication
from client.app.services.mqtt_service import mqtt_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/stations",
    response_model=StationList,
    summary="Listar todas as estações",
    description="""
    Retorna uma lista de todas as estações de carregamento disponíveis em todos os servidores.
    
    Esta rota consulta todos os servidores configurados e retorna uma lista consolidada
    de todas as estações disponíveis, incluindo informações como:
    - Nome da estação
    - Localização
    - Status de disponibilidade
    - Servidor responsável
    
    Returns:
        StationList: Lista de estações e total de registros encontrados
        
    Raises:
        HTTPException: Em caso de erro na comunicação com os servidores
    """
)
async def get_all_stations():
    """
    Endpoint para listar todas as estações disponíveis.
    
    Returns:
        StationList: Lista de estações e total de registros
    """
    try:
        stations = await server_communication.get_all_stations()
        return StationList(stations=stations, total=len(stations))
    except Exception as e:
        logger.error(f"Erro ao obter estações: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao obter estações")


@router.post(
    "/stations/reserve",
    response_model=ReservationResponse,
    summary="Reservar uma estação",
    description="""
    Realiza a reserva de uma estação de carregamento em qualquer servidor disponível.
    
    Esta rota realiza as seguintes operações:
    1. Publica a solicitação de reserva via MQTT para todos os servidores
    2. Tenta realizar a reserva em todos os servidores disponíveis
    3. Retorna o resultado da primeira reserva bem-sucedida
    
    O processo de reserva é atômico, garantindo que apenas um cliente possa
    reservar uma estação específica em um determinado horário.
    
    Parameters:
        reservation (ReservationRequest): Dados da solicitação de reserva
        
    Returns:
        ReservationResponse: Resultado da tentativa de reserva, incluindo:
            - Status de sucesso
            - Mensagem descritiva
            - ID da reserva (se bem-sucedida)
            - Dados da estação reservada (se bem-sucedida)
            
    Raises:
        HTTPException: Em caso de erro durante o processo de reserva
    """
)
async def reserve_station(reservation: ReservationRequest):
    """
    Endpoint para reservar uma estação de carregamento.
    
    Args:
        reservation (ReservationRequest): Dados da reserva
        
    Returns:
        ReservationResponse: Resultado da tentativa de reserva
    """
    try:
        # Publica a solicitação de reserva via MQTT
        mqtt_service.publish(
            "stations/reserve",
            reservation.model_dump()
        )

        # Tenta reservar em todos os servidores
        responses = await server_communication.broadcast_reservation(
            reservation.model_dump()
        )

        if not responses:
            return ReservationResponse(
                success=False,
                message="Nenhum servidor disponível para realizar a reserva"
            )

        # Retorna a primeira resposta bem-sucedida
        successful_response = next(
            (r for r in responses if r.get("success", False)),
            None
        )

        if successful_response:
            return ReservationResponse(
                success=True,
                message="Reserva realizada com sucesso",
                reservation_id=successful_response.get("reservation_id"),
                station=successful_response.get("station")
            )
        else:
            return ReservationResponse(
                success=False,
                message="Não foi possível realizar a reserva em nenhum servidor"
            )

    except Exception as e:
        logger.error(f"Erro ao realizar reserva: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao realizar reserva"
        )
