from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    carro_id = Column(Integer, ForeignKey("carros.id"))
    ponto_carregamento_id = Column(Integer, ForeignKey("pontos_carregamento.id"))
    inicio_previsto = Column(DateTime(timezone=True))
    fim_previsto = Column(DateTime(timezone=True))
    status = Column(String)  # "pendente", "confirmada", "em_andamento", "concluida", "cancelada"
    energia_necessaria = Column(Float)  # em kWh
    servidor_origem = Column(String)  # ID do servidor que recebeu a reserva
    servidores_envolvidos = Column(JSON)  # Lista de servidores envolvidos na reserva
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacionamentos
    carro = relationship("Carro")
    ponto_carregamento = relationship("PontoCarregamento", back_populates="reservas")

class SequenciaReserva(Base):
    __tablename__ = "sequencias_reserva"

    id = Column(Integer, primary_key=True, index=True)
    reserva_principal_id = Column(Integer, ForeignKey("reservas.id"))
    servidor_destino = Column(String)  # ID do servidor que gerencia o próximo ponto
    status = Column(String)  # "pendente", "confirmada", "cancelada"
    ordem = Column(Integer)  # Ordem na sequência de reservas
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacionamentos
    reserva_principal = relationship("Reserva") 