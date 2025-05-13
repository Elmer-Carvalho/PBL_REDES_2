from typing import List
import os
from dotenv import load_dotenv
from pydantic.v1 import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "Sistema de Reserva de Postos"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Configurações do banco de dados
    SQLITE_DATABASE_URL: str = "sqlite:///./charging_stations.db"

    # Configurações MQTT
    MQTT_BROKER: str = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_CLIENT_ID: str = os.getenv("MQTT_CLIENT_ID", "client_api")

    # Lista de servidores disponíveis
    AVAILABLE_SERVERS: List[str] = [
        "http://server1:8001",
        "http://server2:8002",
        "http://server3:8003"
    ]

    class Config:
        case_sensitive = True


settings = Settings()
