import gmqtt
from ..config import get_settings
import json
import structlog
from typing import Callable, Dict, Any, Pattern
import asyncio
import re
from datetime import datetime

settings = get_settings()

# Configuração do logging estruturado
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

class MQTTClient:
    def __init__(self):
        self.client = None
        self.handlers: Dict[str, Callable] = {}
        self.connected = False
        self.client_id = settings.MQTT_CLIENT_ID
        self.broker = settings.MQTT_BROKER
        self.port = settings.MQTT_PORT
        self.responses: Dict[str, Any] = {}

    async def connect(self):
        """Tenta conectar ao broker com retry"""
        while not self.client.is_connected:
            try:
                await self.client.connect(self.broker, self.port)
                break
            except Exception as e:
                logger.warning("broker_unavailable", error=str(e), retry_in="3s")
                await asyncio.sleep(3)

    async def _on_connect(self, client, flags, rc, properties):
        """Implementação assíncrona do on_connect"""
        if rc == 0:
            self.connected = True
            logger.info("mqtt_connected", client_id=self.client_id)
            # Inscreve-se nos tópicos relevantes
            topics = [
                ("carros/+/status", 0),
                ("carros/+/bateria", 0),
                ("pontos/+/disponibilidade", 0),
                ("reservas/+/status", 0),
                ("server/postos/request", 0),
                ("server/postos/reserva", 0)
            ]
            for topic, qos in topics:
                self.client.subscribe(topic, qos)
            logger.info("topics_subscribed", client_id=self.client_id)
        else:
            logger.error("mqtt_connection_failed", code=rc, client_id=self.client_id)

    def on_connect(self, client, flags, rc, properties):
        """Callback síncrono para o gmqtt"""
        asyncio.create_task(self._on_connect(client, flags, rc, properties))

    async def on_message(self, client, topic, payload, qos, properties):
        logger.info(f"[MQTT RECEBIDO] Tópico: {topic} | Payload: {payload.decode()}")
        try:
            logger.info("message_received", topic=topic, client_id=self.client_id)
            payload_str = payload.decode()
            payload_data = json.loads(payload_str)
            payload_data["timestamp"] = datetime.now().isoformat()

            # Procura por um handler que corresponda ao tópico usando regex
            matched_handler = None
            for pattern, handler in self.handlers.items():
                if re.match(pattern.replace("+", "[^/]+"), topic):
                    matched_handler = handler
                    break

            if matched_handler:
                logger.info("handler_found", topic=topic, client_id=self.client_id)
                await matched_handler(payload_data)
            else:
                logger.warning("no_handler_found", topic=topic, client_id=self.client_id)

        except json.JSONDecodeError:
            logger.error("json_decode_error", payload=payload, client_id=self.client_id)
        except Exception as e:
            logger.error("message_processing_error", error=str(e), client_id=self.client_id)

    async def on_disconnect(self, client, packet, exc=None):
        self.connected = False
        if exc:
            logger.warning("unexpected_disconnect", error=str(exc), client_id=self.client_id)
        else:
            logger.info("disconnected", client_id=self.client_id)

    def register_handler(self, topic: str, handler: Callable):
        """Registra um handler para um tópico específico"""
        self.handlers[topic] = handler
        logger.info("handler_registered", topic=topic, client_id=self.client_id)

    async def wait_for_response(self, request_id: str, timeout: float = 5.0):
        """Espera por uma resposta específica com timeout"""
        while self.responses.get(request_id) is None:
            await asyncio.sleep(0.1)
        return self.responses.pop(request_id)

    async def publish(self, topic: str, payload: Dict[str, Any], wait_response: bool = False):
        """Publica uma mensagem em um tópico com suporte opcional a espera por resposta"""
        try:
            if not self.connected:
                logger.warning("client_not_connected", client_id=self.client_id)
                return

            if wait_response:
                request_id = str(datetime.now().timestamp())
                payload["request_id"] = request_id
                self.responses[request_id] = None

            message = json.dumps(payload)
            self.client.publish(topic, message.encode(), qos=1)
            logger.debug("message_published", topic=topic, client_id=self.client_id)

            if wait_response:
                try:
                    response = await asyncio.wait_for(
                        self.wait_for_response(request_id),
                        timeout=5.0
                    )
                    return response
                except asyncio.TimeoutError:
                    logger.warning("response_timeout", request_id=request_id, client_id=self.client_id)
                    return {"erro": "Timeout: Sem resposta do servidor solicitado"}

        except Exception as e:
            logger.error("publish_error", error=str(e), client_id=self.client_id)

    async def start(self):
        """Inicia o cliente MQTT"""
        try:
            self.client = gmqtt.Client(self.client_id)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            await self.connect()
            logger.info("mqtt_client_started", client_id=self.client_id)
        except Exception as e:
            logger.error("mqtt_start_error", error=str(e), client_id=self.client_id)

    async def stop(self):
        """Para o cliente MQTT"""
        try:
            if self.client:
                await self.client.disconnect()
            logger.info("mqtt_client_stopped", client_id=self.client_id)
        except Exception as e:
            logger.error("mqtt_stop_error", error=str(e), client_id=self.client_id)

# Instância global do cliente MQTT
mqtt_client = MQTTClient() 