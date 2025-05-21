import gmqtt
import json
import logging
import asyncio
from app.core import config

logger = logging.getLogger(__name__)

class MQTTService:
    def __init__(self):
        self.client = None
        self.handlers = {}
        self.client_id = config.MQTT_CLIENT_ID
        self.broker = config.MQTT_BROKER
        self.port = config.MQTT_PORT

    def on_connect(self, client, flags, rc, properties):
        """Callback síncrono para o gmqtt"""
        asyncio.create_task(self._on_connect(client, flags, rc, properties))

    async def _on_connect(self, client, flags, rc, properties):
        """Implementação assíncrona do on_connect"""
        logger.info(f"Conectado ao broker MQTT com código: {rc}")

    async def on_message(self, client, topic, payload, qos, properties):
        try:
            payload_str = payload.decode()
            logger.info(f"[MQTT] Mensagem recebida no tópico {topic}: {payload_str}")
            logger.info(f"[MQTT] Handlers registrados: {list(self.handlers.keys())}")
            if topic in self.handlers:
                payload_data = json.loads(payload_str)
                await self.handlers[topic](payload_data)
                logger.info(f"Handler executado com sucesso para o tópico: {topic}")
            else:
                logger.warning(f"Nenhum handler para o tópico: {topic}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem do tópico {topic}: {str(e)}")

    async def connect(self):
        try:
            self.client = gmqtt.Client(self.client_id)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            
            await self.client.connect(self.broker, self.port)
            logger.info("Conectado ao broker MQTT")
        except Exception as e:
            logger.error(f"Erro ao conectar ao broker MQTT: {str(e)}")

    async def publish(self, topic, message):
        try:
            if not self.client:
                logger.error("Cliente MQTT não está conectado")
                return
                
            self.client.publish(topic, json.dumps(message).encode(), qos=1)
            logger.info(f"Mensagem publicada no tópico {topic}: {message}")
        except Exception as e:
            logger.error(f"Erro ao publicar mensagem no tópico {topic}: {str(e)}")

    async def subscribe(self, topic, handler):
        """Inscreve-se em um tópico e registra o handler"""
        try:
            if not self.client:
                logger.error("Cliente MQTT não está conectado")
                return
                
            self.handlers[topic] = handler
            self.client.subscribe(topic, qos=1)
            logger.info(f"Inscrito no tópico: {topic} com handler: {handler.__name__}")
        except Exception as e:
            logger.error(f"Erro ao se inscrever no tópico {topic}: {str(e)}")

    async def disconnect(self):
        try:
            if self.client:
                await self.client.disconnect()
            logger.info("Desconectado do broker MQTT")
        except Exception as e:
            logger.error(f"Erro ao desconectar do broker MQTT: {str(e)}")

# Instância global do serviço MQTT
mqtt_service = MQTTService() 