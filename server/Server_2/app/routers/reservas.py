from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import httpx
from ..database import get_db
from ..models.reserva import Reserva, SequenciaReserva
from ..models.ponto_carregamento import PontoCarregamento
from ..mqtt.client import mqtt_client
from ..config import get_settings

router = APIRouter()
settings = get_settings()

async def verificar_disponibilidade_ponto(
    ponto_id: int,
    inicio: datetime,
    fim: datetime,
    db: Session
) -> bool:
    """Verifica se um ponto está disponível em um período específico"""
    # Verifica se o ponto existe e está disponível
    ponto = db.query(PontoCarregamento).filter(
        PontoCarregamento.id == ponto_id,
        PontoCarregamento.disponivel == True,
        PontoCarregamento.em_manutencao == False
    ).first()
    
    if not ponto:
        return False
    
    # Verifica se há reservas conflitantes
    reserva_conflitante = db.query(Reserva).filter(
        Reserva.ponto_carregamento_id == ponto_id,
        Reserva.status.in_(["pendente", "confirmada", "em_andamento"]),
        (
            (Reserva.inicio_previsto <= inicio) & (Reserva.fim_previsto >= inicio) |
            (Reserva.inicio_previsto <= fim) & (Reserva.fim_previsto >= fim) |
            (Reserva.inicio_previsto >= inicio) & (Reserva.fim_previsto <= fim)
        )
    ).first()
    
    return not bool(reserva_conflitante)

@router.post("/", response_model=dict)
async def criar_reserva(
    carro_id: int,
    ponto_id: int,
    inicio_previsto: datetime,
    fim_previsto: datetime,
    energia_necessaria: float,
    servidores_envolvidos: List[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Cria uma nova reserva de ponto de carregamento"""
    try:
        # Verifica disponibilidade do ponto
        disponivel = await verificar_disponibilidade_ponto(
            ponto_id, inicio_previsto, fim_previsto, db
        )
        
        if not disponivel:
            raise HTTPException(
                status_code=400,
                detail="Ponto de carregamento não está disponível no período solicitado"
            )
        
        # Cria a reserva
        nova_reserva = Reserva(
            carro_id=carro_id,
            ponto_carregamento_id=ponto_id,
            inicio_previsto=inicio_previsto,
            fim_previsto=fim_previsto,
            energia_necessaria=energia_necessaria,
            status="pendente",
            servidor_origem=settings.SERVER_ID,
            servidores_envolvidos=json.dumps(servidores_envolvidos or [])
        )
        
        db.add(nova_reserva)
        db.commit()
        db.refresh(nova_reserva)
        
        # Se houver servidores envolvidos, tenta confirmar as reservas neles
        if servidores_envolvidos:
            for servidor in servidores_envolvidos:
                sequencia = SequenciaReserva(
                    reserva_principal_id=nova_reserva.id,
                    servidor_destino=servidor["id"],
                    status="pendente",
                    ordem=servidor["ordem"]
                )
                db.add(sequencia)
            
            db.commit()
            
            # Tenta confirmar as reservas nos outros servidores
            async with httpx.AsyncClient() as client:
                for servidor in servidores_envolvidos:
                    try:
                        response = await client.post(
                            f"{servidor['url']}/reservas/confirmar",
                            json={
                                "reserva_principal_id": nova_reserva.id,
                                "carro_id": carro_id,
                                "ponto_id": servidor["ponto_id"],
                                "inicio_previsto": servidor["inicio_previsto"],
                                "fim_previsto": servidor["fim_previsto"],
                                "energia_necessaria": servidor["energia_necessaria"]
                            }
                        )
                        
                        if response.status_code == 200:
                            sequencia = db.query(SequenciaReserva).filter(
                                SequenciaReserva.reserva_principal_id == nova_reserva.id,
                                SequenciaReserva.servidor_destino == servidor["id"]
                            ).first()
                            sequencia.status = "confirmada"
                            db.commit()
                        else:
                            # Se alguma reserva falhar, cancela todas
                            await cancelar_reserva(nova_reserva.id, db)
                            raise HTTPException(
                                status_code=400,
                                detail=f"Falha ao confirmar reserva no servidor {servidor['id']}"
                            )
                            
                    except Exception as e:
                        await cancelar_reserva(nova_reserva.id, db)
                        raise HTTPException(
                            status_code=500,
                            detail=f"Erro ao comunicar com servidor {servidor['id']}: {str(e)}"
                        )
        
        # Atualiza o status da reserva principal
        nova_reserva.status = "confirmada"
        db.commit()
        
        # Notifica outros servidores
        mqtt_client.publish(
            f"reservas/{nova_reserva.id}/status",
            {
                "reserva_id": nova_reserva.id,
                "status": nova_reserva.status,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return {
            "mensagem": "Reserva criada e confirmada com sucesso",
            "reserva": {
                "id": nova_reserva.id,
                "carro_id": nova_reserva.carro_id,
                "ponto_id": nova_reserva.ponto_carregamento_id,
                "inicio": nova_reserva.inicio_previsto.isoformat(),
                "fim": nova_reserva.fim_previsto.isoformat(),
                "status": nova_reserva.status
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[dict])
async def listar_reservas(
    status: str = None,
    carro_id: int = None,
    db: Session = Depends(get_db)
):
    """Lista todas as reservas com filtros opcionais"""
    query = db.query(Reserva)
    
    if status:
        query = query.filter(Reserva.status == status)
    if carro_id:
        query = query.filter(Reserva.carro_id == carro_id)
    
    reservas = query.all()
    return [
        {
            "id": reserva.id,
            "carro_id": reserva.carro_id,
            "ponto_id": reserva.ponto_carregamento_id,
            "inicio": reserva.inicio_previsto.isoformat(),
            "fim": reserva.fim_previsto.isoformat(),
            "energia_necessaria": reserva.energia_necessaria,
            "status": reserva.status,
            "servidor_origem": reserva.servidor_origem,
            "servidores_envolvidos": json.loads(reserva.servidores_envolvidos)
        }
        for reserva in reservas
    ]

@router.get("/{reserva_id}", response_model=dict)
async def obter_reserva(reserva_id: int, db: Session = Depends(get_db)):
    """Obtém informações de uma reserva específica"""
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    if not reserva:
        raise HTTPException(
            status_code=404,
            detail=f"Reserva {reserva_id} não encontrada"
        )
    
    # Obtém as sequências de reserva
    sequencias = db.query(SequenciaReserva).filter(
        SequenciaReserva.reserva_principal_id == reserva_id
    ).all()
    
    return {
        "id": reserva.id,
        "carro_id": reserva.carro_id,
        "ponto_id": reserva.ponto_carregamento_id,
        "inicio": reserva.inicio_previsto.isoformat(),
        "fim": reserva.fim_previsto.isoformat(),
        "energia_necessaria": reserva.energia_necessaria,
        "status": reserva.status,
        "servidor_origem": reserva.servidor_origem,
        "servidores_envolvidos": json.loads(reserva.servidores_envolvidos),
        "sequencias": [
            {
                "id": seq.id,
                "servidor_destino": seq.servidor_destino,
                "status": seq.status,
                "ordem": seq.ordem
            }
            for seq in sequencias
        ]
    }

async def cancelar_reserva(reserva_id: int, db: Session):
    """Cancela uma reserva e suas sequências"""
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    if not reserva:
        return
    
    try:
        # Cancela a reserva principal
        reserva.status = "cancelada"
        
        # Cancela as sequências
        sequencias = db.query(SequenciaReserva).filter(
            SequenciaReserva.reserva_principal_id == reserva_id
        ).all()
        
        for sequencia in sequencias:
            sequencia.status = "cancelada"
            
            # Notifica o servidor de destino sobre o cancelamento
            if sequencia.servidor_destino != settings.SERVER_ID:
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"{sequencia.servidor_destino}/reservas/{reserva_id}/cancelar"
                        )
                except Exception as e:
                    logger.error(f"Erro ao notificar cancelamento: {str(e)}")
        
        db.commit()
        
        # Notifica outros servidores
        mqtt_client.publish(
            f"reservas/{reserva_id}/status",
            {
                "reserva_id": reserva_id,
                "status": "cancelada",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{reserva_id}/cancelar", response_model=dict)
async def cancelar_reserva_endpoint(
    reserva_id: int,
    db: Session = Depends(get_db)
):
    """Endpoint para cancelar uma reserva"""
    try:
        await cancelar_reserva(reserva_id, db)
        return {
            "mensagem": "Reserva cancelada com sucesso",
            "reserva_id": reserva_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/confirmar", response_model=dict)
async def confirmar_reserva_sequencia(
    reserva_principal_id: int,
    carro_id: int,
    ponto_id: int,
    inicio_previsto: datetime,
    fim_previsto: datetime,
    energia_necessaria: float,
    db: Session = Depends(get_db)
):
    """Endpoint para confirmar uma reserva em sequência"""
    try:
        # Verifica disponibilidade
        disponivel = await verificar_disponibilidade_ponto(
            ponto_id, inicio_previsto, fim_previsto, db
        )
        
        if not disponivel:
            raise HTTPException(
                status_code=400,
                detail="Ponto de carregamento não está disponível no período solicitado"
            )
        
        # Cria a reserva local
        nova_reserva = Reserva(
            carro_id=carro_id,
            ponto_carregamento_id=ponto_id,
            inicio_previsto=inicio_previsto,
            fim_previsto=fim_previsto,
            energia_necessaria=energia_necessaria,
            status="confirmada",
            servidor_origem=settings.SERVER_ID,
            servidores_envolvidos="[]"  # Reserva local
        )
        
        db.add(nova_reserva)
        db.commit()
        
        return {
            "mensagem": "Reserva confirmada com sucesso",
            "reserva_id": nova_reserva.id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 