from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class PontoCarregamento(Base):
    __tablename__ = "pontos_carregamento"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    localizacao = Column(String)  # Endereço ou coordenadas
    potencia_maxima = Column(Float)  # em kW
    tipo_conector = Column(String)  # Tipo do conector (CCS, CHAdeMO, etc)
    disponivel = Column(Boolean, default=True)
    em_manutencao = Column(Boolean, default=False)
    preco_kwh = Column(Float)  # Preço por kWh
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacionamentos
    reservas = relationship("Reserva", back_populates="ponto_carregamento")
    carregamentos_ativos = relationship("CarregamentoAtivo", back_populates="ponto_carregamento")

class CarregamentoAtivo(Base):
    __tablename__ = "carregamentos_ativos"

    id = Column(Integer, primary_key=True, index=True)
    ponto_carregamento_id = Column(Integer, ForeignKey("pontos_carregamento.id"))
    carro_id = Column(Integer, ForeignKey("carros.id"))
    inicio_carregamento = Column(DateTime(timezone=True), server_default=func.now())
    fim_carregamento = Column(DateTime(timezone=True), nullable=True)
    energia_fornecida = Column(Float, default=0.0)  # em kWh
    status = Column(String)  # "em_andamento", "concluido", "cancelado"
    
    # Relacionamentos
    ponto_carregamento = relationship("PontoCarregamento", back_populates="carregamentos_ativos")
    carro = relationship("Carro") 