import gmqtt
from ..config import get_settings
import json
import logging
from typing import Callable, Dict, Any
import asyncio
from datetime import datetime

settings = get_settings()
logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self):
        self.client = None
        self.handlers: Dict[str, Callable] = {}
        self.connected = False
        self.client_id = settings.MQTT_CLIENT_ID
        self.broker = settings.MQTT_BROKER
        self.port = settings.MQTT_PORT

    def on_connect(self, client, flags, rc, properties):
        """Callback síncrono para o gmqtt"""
        asyncio.create_task(self._on_connect(client, flags, rc, properties))

    async def _on_connect(self, client, flags, rc, properties):
        """Implementação assíncrona do on_connect"""
        if rc == 0:
            self.connected = True
            logger.info("Conectado ao broker MQTT")
            # Inscreve-se nos tópicos relevantes
            topics = [
                ("carros/+/status", 0),
                ("carros/+/bateria", 0),
                ("pontos/+/disponibilidade", 0),
                ("reservas/+/status", 0),
                ("server/postos/request", 0)
            ]
            for topic, qos in topics:
                self.client.subscribe(topic, qos)
            logger.info("Inscrito em todos os tópicos necessários")
        else:
            logger.error(f"Falha na conexão MQTT com código: {rc}")

    async def on_message(self, client, topic, payload, qos, properties):
        try:
            logger.info(f"Mensagem recebida no tópico: {topic}")
            payload_str = payload.decode()
            payload_data = json.loads(payload_str)
            logger.info(f"Payload recebido: {payload_data}")
            payload_data["timestamp"] = datetime.now().isoformat()

            handler = self.handlers.get(topic)
            if handler:
                logger.info(f"Chamando handler para o tópico: {topic}")
                await handler(payload_data)
            else:
                logger.warning(f"Nenhum handler registrado para o tópico: {topic}")

        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar mensagem JSON: {payload}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem MQTT: {str(e)}")

    async def on_disconnect(self, client, packet, exc=None):
        self.connected = False
        if exc:
            logger.warning(f"Desconectado inesperadamente do broker MQTT: {exc}")
        else:
            logger.info("Desconectado do broker MQTT")

    def register_handler(self, topic: str, handler: Callable):
        """Registra um handler para um tópico específico"""
        self.handlers[topic] = handler
        logger.info(f"Handler registrado para o tópico: {topic}")

    async def publish(self, topic: str, payload: Dict[str, Any]):
        """Publica uma mensagem em um tópico"""
        try:
            if not self.connected:
                logger.warning("Cliente MQTT não está conectado")
                return
                
            message = json.dumps(payload)
            self.client.publish(topic, message.encode(), qos=1)
            logger.debug(f"Mensagem publicada no tópico {topic}: {message}")
        except Exception as e:
            logger.error(f"Erro ao publicar mensagem MQTT: {str(e)}")

    async def start(self):
        """Inicia o cliente MQTT"""
        try:
            self.client = gmqtt.Client(self.client_id)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            await self.client.connect(self.broker, self.port)
            logger.info("Cliente MQTT iniciado")
        except Exception as e:
            logger.error(f"Erro ao iniciar cliente MQTT: {str(e)}")

    async def stop(self):
        """Para o cliente MQTT"""
        try:
            if self.client:
                await self.client.disconnect()
            logger.info("Cliente MQTT parado")
        except Exception as e:
            logger.error(f"Erro ao parar cliente MQTT: {str(e)}")

# Instância global do cliente MQTT
mqtt_client = MQTTClient() 