from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.ponto_carregamento import PontoCarregamento

router = APIRouter()

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