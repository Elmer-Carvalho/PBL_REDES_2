import paho.mqtt.client as mqtt
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
        self.client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.handlers: Dict[str, Callable] = {}
        self.connected = False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logger.info("Conectado ao broker MQTT")
            # Inscreve-se nos tópicos relevantes
            self.client.subscribe([
                ("carros/+/status", 0),
                ("carros/+/bateria", 0),
                ("pontos/+/disponibilidade", 0),
                ("reservas/+/status", 0)
            ])
        else:
            logger.error(f"Falha na conexão MQTT com código: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            # Adiciona timestamp ao payload
            payload["timestamp"] = datetime.now().isoformat()
            
            # Processa a mensagem com o handler apropriado
            if topic in self.handlers:
                asyncio.create_task(self.handlers[topic](payload))
            else:
                logger.warning(f"Nenhum handler registrado para o tópico: {topic}")
                
        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar mensagem JSON: {msg.payload}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem MQTT: {str(e)}")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            logger.warning(f"Desconectado inesperadamente do broker MQTT. Código: {rc}")
        else:
            logger.info("Desconectado do broker MQTT")

    def register_handler(self, topic: str, handler: Callable):
        """Registra um handler para um tópico específico"""
        self.handlers[topic] = handler
        logger.info(f"Handler registrado para o tópico: {topic}")

    def publish(self, topic: str, payload: Dict[str, Any]):
        """Publica uma mensagem em um tópico"""
        try:
            if not self.connected:
                logger.warning("Cliente MQTT não está conectado")
                return
                
            message = json.dumps(payload)
            self.client.publish(topic, message)
            logger.debug(f"Mensagem publicada no tópico {topic}: {message}")
        except Exception as e:
            logger.error(f"Erro ao publicar mensagem MQTT: {str(e)}")

    def start(self):
        """Inicia o cliente MQTT"""
        try:
            self.client.connect(settings.MQTT_BROKER, settings.MQTT_PORT)
            self.client.loop_start()
            logger.info("Cliente MQTT iniciado")
        except Exception as e:
            logger.error(f"Erro ao iniciar cliente MQTT: {str(e)}")

    def stop(self):
        """Para o cliente MQTT"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Cliente MQTT parado")
        except Exception as e:
            logger.error(f"Erro ao parar cliente MQTT: {str(e)}")

# Instância global do cliente MQTT
mqtt_client = MQTTClient() 