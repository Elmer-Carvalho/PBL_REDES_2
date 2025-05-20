from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from ..database import Base

class Carro(Base):
    __tablename__ = "carros"

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String, unique=True, index=True)
    modelo = Column(String)
    capacidade_bateria = Column(Float)  # em kWh
    nivel_bateria_atual = Column(Float)  # em kWh
    taxa_descarga = Column(Float)  # kWh/km
    em_carregamento = Column(Boolean, default=False)
    ultima_atualizacao = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 