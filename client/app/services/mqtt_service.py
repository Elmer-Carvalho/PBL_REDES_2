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
        asyncio.create_task(self._on_connect(client, flags, rc, properties))

    async def _on_connect(self, client, flags, rc, properties):
        if rc == 0:
            logger.info("Conectado ao broker MQTT")
        else:
            logger.error(f"Falha ao conectar ao broker MQTT. Código: {rc}")

    async def on_message(self, client, topic, payload, qos, properties):
        try:
            payload_str = payload.decode()
            if topic in self.handlers:
                payload_data = json.loads(payload_str)
                await self.handlers[topic](payload_data)
            else:
                logger.warning(f"Nenhum handler registrado para o tópico: {topic}")
        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar JSON do tópico {topic}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem do tópico {topic}: {str(e)}")

    async def connect(self):
        try:
            self.client = gmqtt.Client(self.client_id)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            await self.client.connect(self.broker, self.port)
        except Exception as e:
            logger.error(f"Erro ao conectar ao broker MQTT: {str(e)}")
            raise

    async def publish(self, topic, message):
        if not self.client:
            raise RuntimeError("Cliente MQTT não está conectado")
            
        try:
            self.client.publish(topic, json.dumps(message).encode(), qos=1)
            logger.info(f"Mensagem publicada no tópico {topic}")
        except Exception as e:
            logger.error(f"Erro ao publicar mensagem no tópico {topic}: {str(e)}")
            raise

    async def subscribe(self, topic, handler):
        if not self.client:
            raise RuntimeError("Cliente MQTT não está conectado")
            
        try:
            self.handlers[topic] = handler
            self.client.subscribe(topic, qos=1)
            logger.info(f"Inscrito no tópico: {topic}")
        except Exception as e:
            logger.error(f"Erro ao se inscrever no tópico {topic}: {str(e)}")
            raise

    async def disconnect(self):
        if self.client:
            try:
                await self.client.disconnect()
                logger.info("Desconectado do broker MQTT")
            except Exception as e:
                logger.error(f"Erro ao desconectar do broker MQTT: {str(e)}")
                raise

# Instância global do serviço MQTT
mqtt_service = MQTTService() 