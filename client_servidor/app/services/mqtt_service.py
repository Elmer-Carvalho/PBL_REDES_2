import paho.mqtt.client as mqtt
import json
import logging
from app.core import config

logger = logging.getLogger(__name__)

class MQTTService:
    def __init__(self):
        self.client = mqtt.Client(client_id=config.MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.handlers = {}

    def connect(self):
        self.client.connect(config.MQTT_BROKER, config.MQTT_PORT)
        self.client.loop_start()
        logger.info("Conectado ao broker MQTT")

    def on_connect(self, client, userdata, flags, rc):
        logger.info(f"Conectado ao broker MQTT com código: {rc}")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        logger.info(f"[MQTT] Mensagem recebida no tópico {topic}: {payload}")
        try:
            if topic in self.handlers:
                self.handlers[topic](json.loads(payload))
                logger.info(f"Handler executado com sucesso para o tópico: {topic}")
            else:
                logger.warning(f"Nenhum handler para o tópico: {topic}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem do tópico {topic}: {str(e)}")

    def publish(self, topic, message):
        try:
            self.client.publish(topic, json.dumps(message))
            logger.info(f"Mensagem publicada no tópico {topic}: {message}")
        except Exception as e:
            logger.error(f"Erro ao publicar mensagem no tópico {topic}: {str(e)}")

    def subscribe(self, topic, handler):
        try:
            self.handlers[topic] = handler
            self.client.subscribe(topic)
            logger.info(f"Inscrito no tópico: {topic} com handler: {handler.__name__}")
        except Exception as e:
            logger.error(f"Erro ao se inscrever no tópico {topic}: {str(e)}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Desconectado do broker MQTT")

mqtt_service = MQTTService() 