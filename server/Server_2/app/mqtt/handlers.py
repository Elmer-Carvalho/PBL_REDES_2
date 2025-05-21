import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.carro import Carro
from ..models.ponto_carregamento import PontoCarregamento, CarregamentoAtivo
from datetime import datetime
from .client import mqtt_client
from ..config import get_settings
import json

logger = logging.getLogger(__name__)
settings = get_settings()

async def handle_carro_status(payload: Dict[str, Any]):
    """Handler para atualizações de status dos carros"""
    try:
        db = SessionLocal()
        carro = db.query(Carro).filter(Carro.placa == payload["placa"]).first()
        
        if carro:
            carro.nivel_bateria_atual = payload["nivel_bateria"]
            carro.em_carregamento = payload.get("em_carregamento", False)
            carro.ultima_atualizacao = datetime.now()
            db.commit()
            logger.info(f"Status do carro {carro.placa} atualizado")
        else:
            logger.warning(f"Carro com placa {payload['placa']} não encontrado")
            
    except Exception as e:
        logger.error(f"Erro ao processar status do carro: {str(e)}")
    finally:
        db.close()

async def handle_carro_bateria(payload: Dict[str, Any]):
    """Handler para atualizações de nível de bateria"""
    try:
        db = SessionLocal()
        carro = db.query(Carro).filter(Carro.placa == payload["placa"]).first()
        
        if carro:
            carro.nivel_bateria_atual = payload["nivel_bateria"]
            carro.taxa_descarga = payload.get("taxa_descarga", carro.taxa_descarga)
            carro.ultima_atualizacao = datetime.now()
            db.commit()
            
            # Notifica outros servidores sobre a atualização
            mqtt_client.publish(
                f"carros/{carro.placa}/status",
                {
                    "placa": carro.placa,
                    "nivel_bateria": carro.nivel_bateria_atual,
                    "taxa_descarga": carro.taxa_descarga,
                    "timestamp": datetime.now().isoformat()
                }
            )
            logger.info(f"Nível de bateria do carro {carro.placa} atualizado")
        else:
            logger.warning(f"Carro com placa {payload['placa']} não encontrado")
            
    except Exception as e:
        logger.error(f"Erro ao processar atualização de bateria: {str(e)}")
    finally:
        db.close()

async def handle_ponto_disponibilidade(payload: Dict[str, Any]):
    """Handler para atualizações de disponibilidade dos pontos de carregamento"""
    try:
        db = SessionLocal()
        ponto = db.query(PontoCarregamento).filter(
            PontoCarregamento.id == payload["ponto_id"]
        ).first()
        
        if ponto:
            ponto.disponivel = payload["disponivel"]
            ponto.em_manutencao = payload.get("em_manutencao", False)
            db.commit()
            
            # Notifica outros servidores sobre a atualização
            mqtt_client.publish(
                f"pontos/{ponto.id}/status",
                {
                    "ponto_id": ponto.id,
                    "disponivel": ponto.disponivel,
                    "em_manutencao": ponto.em_manutencao,
                    "timestamp": datetime.now().isoformat()
                }
            )
            logger.info(f"Disponibilidade do ponto {ponto.id} atualizada")
        else:
            logger.warning(f"Ponto de carregamento {payload['ponto_id']} não encontrado")
            
    except Exception as e:
        logger.error(f"Erro ao processar disponibilidade do ponto: {str(e)}")
    finally:
        db.close()

async def handle_reserva_status(payload: Dict[str, Any]):
    """Handler para atualizações de status das reservas"""
    try:
        db = SessionLocal()
        # Aqui você implementaria a lógica para atualizar o status da reserva
        # e notificar outros servidores envolvidos
        logger.info(f"Status da reserva {payload['reserva_id']} atualizado")
            
    except Exception as e:
        logger.error(f"Erro ao processar status da reserva: {str(e)}")
    finally:
        db.close()

async def handle_postos_request(payload: Dict[str, Any]):
    logger.info(f"Recebido payload em handle_postos_request: {payload}")
    if payload.get("server_id") != settings.SERVER_ID:
        logger.info(f"Ignorando requisição para outro servidor: {payload.get('server_id')}")
        return

    db = SessionLocal()
    try:
        postos = db.query(PontoCarregamento).all()
        postos_list = [
            {
                "id": p.id,
                "nome": p.nome,
                "localizacao": p.localizacao,
                "potencia_maxima": p.potencia_maxima,
                "tipo_conector": p.tipo_conector,
                "preco_kwh": p.preco_kwh,
                "disponivel": p.disponivel,
                "em_manutencao": p.em_manutencao
            } for p in postos
        ]
        response_topic = f"client/{payload['client_id']}/postos/response"
        response_payload = {
            "request_id": payload["request_id"],
            "postos": postos_list
        }
        logger.info(f"Publicando resposta no tópico: {response_topic}")
        logger.info(f"Payload da resposta: {response_payload}")
        await mqtt_client.publish(response_topic, response_payload)
        logger.info("Resposta publicada com sucesso")
    except Exception as e:
        logger.error(f"Erro ao processar requisição de postos: {str(e)}")
    finally:
        db.close()

def register_handlers():
    """Registra todos os handlers MQTT"""
    mqtt_client.register_handler("carros/+/status", handle_carro_status)
    mqtt_client.register_handler("carros/+/bateria", handle_carro_bateria)
    mqtt_client.register_handler("pontos/+/disponibilidade", handle_ponto_disponibilidade)
    mqtt_client.register_handler("reservas/+/status", handle_reserva_status)
    mqtt_client.register_handler("server/postos/request", handle_postos_request)
    logger.info("Handlers MQTT registrados") 