import httpx
from typing import List, Dict, Any
import logging

from client.app.core.config import settings
from client.app.core.exceptions import ServerCommunicationException

logger = logging.getLogger(__name__)


class ServerCommunicationService:
    """
    Serviço responsável pela comunicação com os servidores de estações.
    
    Este serviço gerencia a comunicação HTTP com os diferentes servidores que
    hospedam as estações de carregamento, permitindo consultas e reservas
    distribuídas.
    
    Attributes:
        servers (List[str]): Lista de URLs dos servidores disponíveis
        client (httpx.AsyncClient): Cliente HTTP assíncrono para comunicação
    """

    def __init__(self):
        """
        Inicializa o serviço com a lista de servidores e um cliente HTTP assíncrono.
        """
        self.servers = settings.AVAILABLE_SERVERS
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_all_stations(self) -> List[Dict[str, Any]]:
        """
        Obtém todas as estações disponíveis em todos os servidores.
        
        Este método consulta cada servidor configurado e consolida as respostas
        em uma única lista de estações.
        
        Returns:
            List[Dict[str, Any]]: Lista de todas as estações disponíveis
            
        Raises:
            ServerCommunicationException: Se houver erro na comunicação com algum servidor
        """
        all_stations = []
        for server in self.servers:
            try:
                response = await self.client.get(f"{server}/api/v1/stations")
                if response.status_code == 200:
                    stations = response.json()
                    all_stations.extend(stations)
                else:
                    logger.warning(f"Erro ao obter estações do servidor {server}: {response.status_code}")
            except Exception as e:
                logger.error(f"Erro na comunicação com o servidor {server}: {str(e)}")
                raise ServerCommunicationException(server)
        return all_stations

    async def reserve_station(self, server: str, reservation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tenta reservar uma estação em um servidor específico.
        
        Args:
            server (str): URL do servidor onde a reserva será tentada
            reservation_data (Dict[str, Any]): Dados da reserva a ser realizada
            
        Returns:
            Dict[str, Any]: Resposta do servidor com o resultado da reserva
            
        Raises:
            ServerCommunicationException: Se houver erro na comunicação com o servidor
        """
        try:
            response = await self.client.post(
                f"{server}/api/v1/stations/reserve",
                json=reservation_data
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro ao reservar estação no servidor {server}: {response.status_code}")
                raise ServerCommunicationException(server)
        except Exception as e:
            logger.error(f"Erro na comunicação com o servidor {server}: {str(e)}")
            raise ServerCommunicationException(server)

    async def broadcast_reservation(self, reservation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Tenta realizar uma reserva em todos os servidores disponíveis.
        
        Este método tenta realizar a reserva em cada servidor configurado,
        coletando todas as respostas, mesmo que alguns servidores falhem.
        
        Args:
            reservation_data (Dict[str, Any]): Dados da reserva a ser realizada
            
        Returns:
            List[Dict[str, Any]]: Lista de respostas de todos os servidores
        """
        responses = []
        for server in self.servers:
            try:
                response = await self.reserve_station(server, reservation_data)
                responses.append(response)
            except ServerCommunicationException:
                continue
        return responses

    async def close(self):
        """
        Fecha o cliente HTTP assíncrono.
        """
        await self.client.aclose()


server_communication = ServerCommunicationService()
