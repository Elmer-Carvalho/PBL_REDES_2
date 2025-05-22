from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Configurações do MQTT
    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883
    CLIENT_ID: str = "client_1"
    
    # Configurações do servidor
    SERVER_1_ID: str = "server_1"
    SERVER_2_ID: str = "server_2"
    
    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings() 