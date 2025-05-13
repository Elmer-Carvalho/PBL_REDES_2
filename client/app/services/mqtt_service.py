import paho.mqtt.client as mqtt
from typing import Callable, Dict, Any
import json
import logging

from client.app.core.config import settings

logger = logging.getLogger(__name__)


class MQTTService:
    """
    Serviço responsável pela comunicação MQTT entre os servidores.
    
    Este serviço gerencia a comunicação assíncrona entre os servidores usando o protocolo MQTT,
    permitindo o broadcast de mensagens e o processamento de eventos em tempo real.
    
    Attributes:
        client (mqtt.Client): Cliente MQTT para comunicação
        message_handlers (Dict[str, Callable]): Dicionário de handlers para diferentes tópicos
    """

    def __init__(self):
        """
        Inicializa o serviço MQTT com um novo cliente e configura os callbacks.
        """
        self.client = mqtt.Client(settings.MQTT_CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.message_handlers: Dict[str, Callable] = {}

    def connect(self):
        """
        Estabelece conexão com o broker MQTT e inicia o loop de eventos.
        
        Raises:
            Exception: Se houver erro na conexão com o broker
        """
        try:
            self.client.connect(settings.MQTT_BROKER, settings.MQTT_PORT)
            self.client.loop_start()
            logger.info("Conectado ao broker MQTT")
        except Exception as e:
            logger.error(f"Erro ao conectar ao broker MQTT: {str(e)}")
            raise

    def on_connect(self, client, userdata, flags, rc):
        """
        Callback chamado quando a conexão com o broker é estabelecida.
        
        Args:
            client: Cliente MQTT
            userdata: Dados do usuário
            flags: Flags de conexão
            rc: Código de retorno da conexão
        """
        if rc == 0:
            logger.info("Conectado ao broker MQTT com sucesso")
            # Inscreve-se em todos os tópicos relevantes
            self.client.subscribe("stations/#")
        else:
            logger.error(f"Falha ao conectar ao broker MQTT com código: {rc}")

    def on_message(self, client, userdata, msg):
        """
        Callback chamado quando uma mensagem é recebida.
        
        Args:
            client: Cliente MQTT
            userdata: Dados do usuário
            msg: Mensagem recebida
        """
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())

            if topic in self.message_handlers:
                self.message_handlers[topic](payload)
            else:
                logger.warning(f"Nenhum handler registrado para o tópico: {topic}")

        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar mensagem MQTT: {msg.payload}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem MQTT: {str(e)}")

    def publish(self, topic: str, message: Dict[str, Any]):
        """
        Publica uma mensagem em um tópico específico.
        
        Args:
            topic (str): Tópico onde a mensagem será publicada
            message (Dict[str, Any]): Mensagem a ser publicada
            
        Raises:
            Exception: Se houver erro ao publicar a mensagem
        """
        try:
            payload = json.dumps(message)
            self.client.publish(topic, payload)
            logger.info(f"Mensagem publicada no tópico {topic}")
        except Exception as e:
            logger.error(f"Erro ao publicar mensagem MQTT: {str(e)}")
            raise

    def register_handler(self, topic: str, handler: Callable):
        """
        Registra um handler para um tópico específico.
        
        Args:
            topic (str): Tópico para o qual o handler será registrado
            handler (Callable): Função que processará as mensagens do tópico
        """
        self.message_handlers[topic] = handler
        self.client.subscribe(topic)
        logger.info(f"Handler registrado para o tópico: {topic}")

    def disconnect(self):
        """
        Desconecta do broker MQTT e para o loop de eventos.
        """
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Desconectado do broker MQTT")


mqtt_service = MQTTService()
