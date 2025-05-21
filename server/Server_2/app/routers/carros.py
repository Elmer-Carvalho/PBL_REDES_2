from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..models.carro import Carro
from ..mqtt.client import mqtt_client

router = APIRouter()

@router.post("/", response_model=dict)
async def criar_carro(
    placa: str,
    modelo: str,
    capacidade_bateria: float,
    nivel_bateria_atual: float,
    taxa_descarga: float,
    db: Session = Depends(get_db)
):
    """Cria um novo carro no sistema"""
    try:
        # Verifica se já existe um carro com a mesma placa
        carro_existente = db.query(Carro).filter(Carro.placa == placa).first()
        if carro_existente:
            raise HTTPException(
                status_code=400,
                detail=f"Já existe um carro cadastrado com a placa {placa}"
            )
        
        # Cria o novo carro
        novo_carro = Carro(
            placa=placa,
            modelo=modelo,
            capacidade_bateria=capacidade_bateria,
            nivel_bateria_atual=nivel_bateria_atual,
            taxa_descarga=taxa_descarga
        )
        
        db.add(novo_carro)
        db.commit()
        db.refresh(novo_carro)
        
        # Notifica outros servidores sobre o novo carro
        mqtt_client.publish(
            f"carros/{placa}/status",
            {
                "placa": placa,
                "nivel_bateria": nivel_bateria_atual,
                "em_carregamento": False,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return {
            "mensagem": "Carro criado com sucesso",
            "carro": {
                "id": novo_carro.id,
                "placa": novo_carro.placa,
                "modelo": novo_carro.modelo,
                "nivel_bateria": novo_carro.nivel_bateria_atual
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[dict])
async def listar_carros(db: Session = Depends(get_db)):
    """Lista todos os carros cadastrados"""
    carros = db.query(Carro).all()
    return [
        {
            "id": carro.id,
            "placa": carro.placa,
            "modelo": carro.modelo,
            "nivel_bateria": carro.nivel_bateria_atual,
            "em_carregamento": carro.em_carregamento,
            "ultima_atualizacao": carro.ultima_atualizacao.isoformat() if carro.ultima_atualizacao else None
        }
        for carro in carros
    ]

@router.get("/{placa}", response_model=dict)
async def obter_carro(placa: str, db: Session = Depends(get_db)):
    """Obtém informações de um carro específico"""
    carro = db.query(Carro).filter(Carro.placa == placa).first()
    if not carro:
        raise HTTPException(
            status_code=404,
            detail=f"Carro com placa {placa} não encontrado"
        )
    
    return {
        "id": carro.id,
        "placa": carro.placa,
        "modelo": carro.modelo,
        "capacidade_bateria": carro.capacidade_bateria,
        "nivel_bateria": carro.nivel_bateria_atual,
        "taxa_descarga": carro.taxa_descarga,
        "em_carregamento": carro.em_carregamento,
        "ultima_atualizacao": carro.ultima_atualizacao.isoformat() if carro.ultima_atualizacao else None
    }

@router.put("/{placa}/bateria", response_model=dict)
async def atualizar_bateria(
    placa: str,
    nivel_bateria: float,
    db: Session = Depends(get_db)
):
    """Atualiza o nível de bateria de um carro"""
    carro = db.query(Carro).filter(Carro.placa == placa).first()
    if not carro:
        raise HTTPException(
            status_code=404,
            detail=f"Carro com placa {placa} não encontrado"
        )
    
    try:
        carro.nivel_bateria_atual = nivel_bateria
        carro.ultima_atualizacao = datetime.now()
        db.commit()
        
        # Notifica outros servidores sobre a atualização
        mqtt_client.publish(
            f"carros/{placa}/bateria",
            {
                "placa": placa,
                "nivel_bateria": nivel_bateria,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return {
            "mensagem": "Nível de bateria atualizado com sucesso",
            "carro": {
                "placa": carro.placa,
                "nivel_bateria": carro.nivel_bateria_atual,
                "ultima_atualizacao": carro.ultima_atualizacao.isoformat()
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 