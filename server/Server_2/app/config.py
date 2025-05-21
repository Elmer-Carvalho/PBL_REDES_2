from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Configurações gerais
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SERVER_ID: str = os.getenv("SERVER_ID", "server2")
    
    # Configurações do banco de dados
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/server2.db")
    
    # Configurações MQTT
    MQTT_BROKER: str = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_CLIENT_ID: str = f"server_{SERVER_ID}"
    
    # Configurações da API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Configurações de segurança
    SECRET_KEY: str = os.getenv("SECRET_KEY", "chave_secreta_temporaria")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings() 