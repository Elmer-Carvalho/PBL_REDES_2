import asyncio
import json
import uuid
import structlog
from typing import Dict, Any, Optional
from datetime import datetime
from .client import MQTTClient
from ..config import get_settings

logger = structlog.get_logger()
settings = get_settings()

class ReservaClient:
    def __init__(self, mqtt_client: MQTTClient):
        self.mqtt_client = mqtt_client
        self.client_id = settings.CLIENT_ID
        self.response_futures: Dict[str, asyncio.Future] = {}

    async def reservar_posto(self, carro: Dict[str, Any], posto_id: int, server_id: str) -> Dict[str, Any]:
        """
        Envia uma requisição para reservar um posto de carregamento
        
        Args:
            carro: Dicionário com informações do carro
            posto_id: ID do posto de carregamento
            server_id: ID do servidor que gerencia o posto
            
        Returns:
            Dict com a resposta da reserva
        """
        request_id = str(uuid.uuid4())
        
        # Cria um Future para aguardar a resposta
        future = asyncio.Future()
        self.response_futures[request_id] = future
        
        # Prepara o payload da requisição
        payload = {
            "request_id": request_id,
            "client_id": self.client_id,
            "server_id": server_id,
            "carro": carro,
            "posto_id": posto_id
        }
        
        # Registra handler para a resposta
        response_topic = f"client/{self.client_id}/postos/reserva/response"
        await self.mqtt_client.register_handler(
            response_topic,
            lambda p: self._handle_response(p, request_id)
        )
        
        # Publica a requisição
        logger.info("enviando_requisicao_reserva", 
                   request_id=request_id,
                   server_id=server_id,
                   posto_id=posto_id)
        await self.mqtt_client.publish(
            "server/postos/reserva",
            payload,
            wait_for_response=True
        )
        
        try:
            # Aguarda a resposta com timeout
            response = await asyncio.wait_for(future, timeout=30.0)
            logger.info("reserva_processada", 
                       request_id=request_id,
                       status=response.get("status"))
            return response
        except asyncio.TimeoutError:
            logger.error("timeout_reserva", 
                        request_id=request_id)
            return {
                "request_id": request_id,
                "status": "erro",
                "mensagem": "Timeout ao aguardar resposta da reserva"
            }
        finally:
            # Limpa o Future e o handler
            self.response_futures.pop(request_id, None)
            await self.mqtt_client.unregister_handler(response_topic)

    def _handle_response(self, payload: Dict[str, Any], request_id: str):
        """Handler para processar respostas de reserva"""
        if payload.get("request_id") == request_id:
            future = self.response_futures.get(request_id)
            if future and not future.done():
                future.set_result(payload)

async def main():
    """Função principal para testar o cliente de reserva"""
    # Configura o cliente MQTT
    mqtt_client = MQTTClient(
        client_id=settings.CLIENT_ID,
        host=settings.MQTT_HOST,
        port=settings.MQTT_PORT
    )
    await mqtt_client.connect()
    
    # Cria o cliente de reserva
    reserva_client = ReservaClient(mqtt_client)
    
    # Dados de teste
    carro = {
        "placa": "ABC1234",
        "modelo": "Tesla Model 3",
        "capacidade_bateria": 75.0,
        "nivel_bateria_atual": 30.0,
        "taxa_descarga": 0.5
    }
    
    # Tenta fazer uma reserva
    response = await reserva_client.reservar_posto(
        carro=carro,
        posto_id=1,
        server_id="server_1"
    )
    
    print(f"Resposta da reserva: {json.dumps(response, indent=2)}")
    
    # Desconecta o cliente
    await mqtt_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 