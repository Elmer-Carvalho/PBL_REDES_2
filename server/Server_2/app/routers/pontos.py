from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy.exc import OperationalError

from ..database import get_db
from ..models.ponto_carregamento import PontoCarregamento, CarregamentoAtivo
from ..mqtt.client import mqtt_client

router = APIRouter()

class ReservaRequest(BaseModel):
    server_id: int
    nome_posto: str
    nome_cliente: str

@router.post("/", response_model=dict)
async def criar_ponto(
    nome: str,
    localizacao: str,
    potencia_maxima: float,
    tipo_conector: str,
    preco_kwh: float,
    db: Session = Depends(get_db)
):
    """Cria um novo ponto de carregamento"""
    try:
        novo_ponto = PontoCarregamento(
            nome=nome,
            localizacao=localizacao,
            potencia_maxima=potencia_maxima,
            tipo_conector=tipo_conector,
            preco_kwh=preco_kwh,
            disponivel=True,
            em_manutencao=False
        )
        
        db.add(novo_ponto)
        db.commit()
        db.refresh(novo_ponto)
        
        # Notifica outros servidores sobre o novo ponto
        mqtt_client.publish(
            f"pontos/{novo_ponto.id}/disponibilidade",
            {
                "ponto_id": novo_ponto.id,
                "disponivel": True,
                "em_manutencao": False,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return {
            "mensagem": "Ponto de carregamento criado com sucesso",
            "ponto": {
                "id": novo_ponto.id,
                "nome": novo_ponto.nome,
                "localizacao": novo_ponto.localizacao,
                "disponivel": novo_ponto.disponivel
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[dict])
async def listar_pontos(
    disponivel: bool = None,
    em_manutencao: bool = None,
    db: Session = Depends(get_db)
):
    """Lista todos os pontos de carregamento com filtros opcionais"""
    query = db.query(PontoCarregamento)
    
    if disponivel is not None:
        query = query.filter(PontoCarregamento.disponivel == disponivel)
    if em_manutencao is not None:
        query = query.filter(PontoCarregamento.em_manutencao == em_manutencao)
    
    pontos = query.all()
    return [
        {
            "id": ponto.id,
            "nome": ponto.nome,
            "localizacao": ponto.localizacao,
            "potencia_maxima": ponto.potencia_maxima,
            "tipo_conector": ponto.tipo_conector,
            "preco_kwh": ponto.preco_kwh,
            "disponivel": ponto.disponivel,
            "em_manutencao": ponto.em_manutencao,
            "ultima_atualizacao": ponto.updated_at.isoformat() if ponto.updated_at else None
        }
        for ponto in pontos
    ]

@router.get("/{ponto_id}", response_model=dict)
async def obter_ponto(ponto_id: int, db: Session = Depends(get_db)):
    """Obtém informações de um ponto de carregamento específico"""
    ponto = db.query(PontoCarregamento).filter(PontoCarregamento.id == ponto_id).first()
    if not ponto:
        raise HTTPException(
            status_code=404,
            detail=f"Ponto de carregamento {ponto_id} não encontrado"
        )
    
    # Obtém carregamentos ativos
    carregamentos_ativos = db.query(CarregamentoAtivo).filter(
        CarregamentoAtivo.ponto_carregamento_id == ponto_id,
        CarregamentoAtivo.status == "em_andamento"
    ).all()
    
    return {
        "id": ponto.id,
        "nome": ponto.nome,
        "localizacao": ponto.localizacao,
        "potencia_maxima": ponto.potencia_maxima,
        "tipo_conector": ponto.tipo_conector,
        "preco_kwh": ponto.preco_kwh,
        "disponivel": ponto.disponivel,
        "em_manutencao": ponto.em_manutencao,
        "carregamentos_ativos": [
            {
                "id": carregamento.id,
                "carro_id": carregamento.carro_id,
                "inicio": carregamento.inicio_carregamento.isoformat(),
                "energia_fornecida": carregamento.energia_fornecida
            }
            for carregamento in carregamentos_ativos
        ],
        "ultima_atualizacao": ponto.updated_at.isoformat() if ponto.updated_at else None
    }

@router.put("/{ponto_id}/disponibilidade", response_model=dict)
async def atualizar_disponibilidade(
    ponto_id: int,
    disponivel: bool,
    em_manutencao: bool = None,
    db: Session = Depends(get_db)
):
    """Atualiza a disponibilidade de um ponto de carregamento"""
    ponto = db.query(PontoCarregamento).filter(PontoCarregamento.id == ponto_id).first()
    if not ponto:
        raise HTTPException(
            status_code=404,
            detail=f"Ponto de carregamento {ponto_id} não encontrado"
        )
    
    try:
        ponto.disponivel = disponivel
        if em_manutencao is not None:
            ponto.em_manutencao = em_manutencao
        db.commit()
        
        # Notifica outros servidores sobre a atualização
        mqtt_client.publish(
            f"pontos/{ponto_id}/disponibilidade",
            {
                "ponto_id": ponto_id,
                "disponivel": disponivel,
                "em_manutencao": ponto.em_manutencao,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return {
            "mensagem": "Disponibilidade atualizada com sucesso",
            "ponto": {
                "id": ponto.id,
                "nome": ponto.nome,
                "disponivel": ponto.disponivel,
                "em_manutencao": ponto.em_manutencao
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{ponto_id}/carregamento", response_model=dict)
async def iniciar_carregamento(
    ponto_id: int,
    carro_id: int,
    db: Session = Depends(get_db)
):
    """Inicia um carregamento em um ponto específico"""
    ponto = db.query(PontoCarregamento).filter(PontoCarregamento.id == ponto_id).first()
    if not ponto:
        raise HTTPException(
            status_code=404,
            detail=f"Ponto de carregamento {ponto_id} não encontrado"
        )
    
    if not ponto.disponivel or ponto.em_manutencao:
        raise HTTPException(
            status_code=400,
            detail="Ponto de carregamento não está disponível"
        )
    
    # Verifica se já existe um carregamento ativo
    carregamento_ativo = db.query(CarregamentoAtivo).filter(
        CarregamentoAtivo.ponto_carregamento_id == ponto_id,
        CarregamentoAtivo.status == "em_andamento"
    ).first()
    
    if carregamento_ativo:
        raise HTTPException(
            status_code=400,
            detail="Ponto de carregamento já está em uso"
        )
    
    try:
        # Cria novo carregamento
        novo_carregamento = CarregamentoAtivo(
            ponto_carregamento_id=ponto_id,
            carro_id=carro_id,
            status="em_andamento"
        )
        
        db.add(novo_carregamento)
        ponto.disponivel = False
        db.commit()
        
        # Notifica outros servidores
        mqtt_client.publish(
            f"pontos/{ponto_id}/carregamento",
            {
                "ponto_id": ponto_id,
                "carro_id": carro_id,
                "acao": "inicio",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return {
            "mensagem": "Carregamento iniciado com sucesso",
            "carregamento": {
                "id": novo_carregamento.id,
                "ponto_id": ponto_id,
                "carro_id": carro_id,
                "inicio": novo_carregamento.inicio_carregamento.isoformat()
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{ponto_id}/carregamento/{carregamento_id}", response_model=dict)
async def finalizar_carregamento(
    ponto_id: int,
    carregamento_id: int,
    energia_fornecida: float,
    db: Session = Depends(get_db)
):
    """Finaliza um carregamento em andamento"""
    carregamento = db.query(CarregamentoAtivo).filter(
        CarregamentoAtivo.id == carregamento_id,
        CarregamentoAtivo.ponto_carregamento_id == ponto_id,
        CarregamentoAtivo.status == "em_andamento"
    ).first()
    
    if not carregamento:
        raise HTTPException(
            status_code=404,
            detail="Carregamento não encontrado ou já finalizado"
        )
    
    try:
        carregamento.status = "concluido"
        carregamento.fim_carregamento = datetime.now()
        carregamento.energia_fornecida = energia_fornecida
        
        # Libera o ponto de carregamento
        ponto = db.query(PontoCarregamento).filter(PontoCarregamento.id == ponto_id).first()
        ponto.disponivel = True
        
        db.commit()
        
        # Notifica outros servidores
        mqtt_client.publish(
            f"pontos/{ponto_id}/carregamento",
            {
                "ponto_id": ponto_id,
                "carro_id": carregamento.carro_id,
                "acao": "fim",
                "energia_fornecida": energia_fornecida,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return {
            "mensagem": "Carregamento finalizado com sucesso",
            "carregamento": {
                "id": carregamento.id,
                "ponto_id": ponto_id,
                "carro_id": carregamento.carro_id,
                "inicio": carregamento.inicio_carregamento.isoformat(),
                "fim": carregamento.fim_carregamento.isoformat(),
                "energia_fornecida": carregamento.energia_fornecida
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reservar")
async def reservar_posto(
    reserva: ReservaRequest,
    db: Session = Depends(get_db)
):
    """Realiza a reserva de um posto de carregamento"""
    # Verifica se o server_id corresponde a este servidor
    if reserva.server_id != 2:  # Este é o Server_2
        return {"message": "Este servidor não é responsável por este posto"}

    try:
        # Tenta obter o posto com bloqueio exclusivo e timeout de 2 segundos
        posto = db.query(PontoCarregamento).with_for_update(skip_locked=True).filter(
            PontoCarregamento.nome == reserva.nome_posto
        ).first()

        if not posto:
            raise HTTPException(status_code=404, detail="Posto não encontrado")

        # Verifica se o posto está disponível
        if not posto.disponivel:
            raise HTTPException(status_code=400, detail="Posto já está ocupado")

        if posto.em_manutencao:
            raise HTTPException(status_code=400, detail="Posto está em manutenção")

        # Calcula as datas de início e fim da reserva
        data_inicio = datetime.now()
        data_fim = data_inicio + timedelta(days=1)

        # Cria a reserva
        nova_reserva = CarregamentoAtivo(
            ponto_carregamento_id=posto.id,
            inicio_carregamento=data_inicio,
            fim_carregamento=data_fim,
            status="em_andamento"
        )

        # Atualiza o status do posto
        posto.disponivel = False

        db.add(nova_reserva)
        db.commit()

        # Notifica outros servidores sobre a reserva
        mqtt_client.publish(
            f"pontos/{posto.id}/reserva",
            {
                "ponto_id": posto.id,
                "disponivel": False,
                "cliente": reserva.nome_cliente,
                "timestamp": datetime.now().isoformat()
            }
        )

        return {
            "message": "Reserva realizada com sucesso",
            "dados_reserva": {
                "posto": reserva.nome_posto,
                "cliente": reserva.nome_cliente,
                "inicio": data_inicio.isoformat(),
                "fim": data_fim.isoformat()
            }
        }

    except OperationalError as e:
        db.rollback()
        # Se o timeout expirar ou não conseguir obter o bloqueio
        raise HTTPException(
            status_code=409,
            detail="Não foi possível processar a reserva. O posto pode estar sendo reservado por outro cliente."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao realizar a reserva") 