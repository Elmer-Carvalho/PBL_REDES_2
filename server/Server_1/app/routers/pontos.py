from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..database import get_db
from ..models.ponto_carregamento import PontoCarregamento, CarregamentoAtivo

router = APIRouter()

class ReservaRequest(BaseModel):
    server_id: int
    nome_posto: str
    nome_cliente: str

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

@router.post("/reservar")
async def reservar_posto(
    reserva: ReservaRequest,
    db: Session = Depends(get_db)
):
    """Realiza a reserva de um posto de carregamento"""
    # Verifica se o server_id corresponde a este servidor
    if reserva.server_id != 1:  # Assumindo que este é o Server_1
        return {"message": "Este servidor não é responsável por este posto"}

    # Busca o posto pelo nome
    posto = db.query(PontoCarregamento).filter(PontoCarregamento.nome == reserva.nome_posto).first()
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

    try:
        db.add(nova_reserva)
        db.commit()
        return {
            "message": "Reserva realizada com sucesso",
            "dados_reserva": {
                "posto": reserva.nome_posto,
                "cliente": reserva.nome_cliente,
                "inicio": data_inicio.isoformat(),
                "fim": data_fim.isoformat()
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao realizar a reserva") 