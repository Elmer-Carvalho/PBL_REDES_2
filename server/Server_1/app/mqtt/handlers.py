import structlog
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from datetime import datetime, timedelta
from ..database import SessionLocal
from ..models.carro import Carro
from ..models.ponto_carregamento import PontoCarregamento, CarregamentoAtivo
from .client import mqtt_client
from ..config import get_settings
import json

logger = structlog.get_logger()
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
            logger.info("carro_status_updated", placa=carro.placa)
        else:
            logger.warning("carro_not_found", placa=payload["placa"])
            
    except Exception as e:
        logger.error("carro_status_error", error=str(e), placa=payload.get("placa"))
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
            await mqtt_client.publish(
                f"carros/{carro.placa}/status",
                {
                    "placa": carro.placa,
                    "nivel_bateria": carro.nivel_bateria_atual,
                    "taxa_descarga": carro.taxa_descarga,
                    "timestamp": datetime.now().isoformat()
                }
            )
            logger.info("bateria_updated", placa=carro.placa)
        else:
            logger.warning("carro_not_found", placa=payload["placa"])
            
    except Exception as e:
        logger.error("bateria_update_error", error=str(e), placa=payload.get("placa"))
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
            await mqtt_client.publish(
                f"pontos/{ponto.id}/status",
                {
                    "ponto_id": ponto.id,
                    "disponivel": ponto.disponivel,
                    "em_manutencao": ponto.em_manutencao,
                    "timestamp": datetime.now().isoformat()
                }
            )
            logger.info("ponto_disponibilidade_updated", ponto_id=ponto.id)
        else:
            logger.warning("ponto_not_found", ponto_id=payload["ponto_id"])
            
    except Exception as e:
        logger.error("ponto_disponibilidade_error", error=str(e), ponto_id=payload.get("ponto_id"))
    finally:
        db.close()

async def handle_reserva_status(payload: Dict[str, Any]):
    """Handler para atualizações de status das reservas"""
    try:
        db = SessionLocal()
        # Aqui você implementaria a lógica para atualizar o status da reserva
        # e notificar outros servidores envolvidos
        logger.info("reserva_status_updated", reserva_id=payload["reserva_id"])
            
    except Exception as e:
        logger.error("reserva_status_error", error=str(e), reserva_id=payload.get("reserva_id"))
    finally:
        db.close()

async def handle_postos_request(payload: Dict[str, Any]):
    logger.info("postos_request_received", payload=payload)
    if payload.get("server_id") != settings.SERVER_ID:
        logger.info("ignoring_other_server_request", server_id=payload.get("server_id"))
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
        logger.info("publishing_response", topic=response_topic)
        await mqtt_client.publish(response_topic, response_payload)
        logger.info("response_published")
    except Exception as e:
        logger.error("postos_request_error", error=str(e))
    finally:
        db.close()

async def handle_reserva_posto(payload: Dict[str, Any]):
    """Handler para processar reservas de postos de carregamento"""
    if payload.get("server_id") != settings.SERVER_ID:
        logger.info("ignoring_other_server_request", server_id=payload.get("server_id"), this_server=settings.SERVER_ID)
        return
    logger.info(f"Reserva recebida no server {settings.SERVER_ID}: {json.dumps(payload, indent=2)}")
    db = SessionLocal()
    try:
        carro_data = payload["carro"]
        placa = carro_data["placa"]
        posto_id = payload["posto_id"]
        request_id = payload["request_id"]
        client_id = payload["client_id"]

        # 1. Verifica se o carro já existe
        carro = db.query(Carro).filter(Carro.placa == placa).first()
        if not carro:
            logger.info("creating_new_car", placa=placa)
            carro = Carro(
                placa=placa,
                modelo=carro_data["modelo"],
                capacidade_bateria=carro_data["capacidade_bateria"],
                nivel_bateria_atual=carro_data["nivel_bateria_atual"],
                taxa_descarga=carro_data["taxa_descarga"],
                em_carregamento=False,
                ultima_atualizacao=datetime.now()
            )
            db.add(carro)
            db.commit()
            db.refresh(carro)
            logger.info("car_created", car_id=carro.id)

        # 2. Verifica se o posto existe
        posto = db.query(PontoCarregamento).filter(PontoCarregamento.id == posto_id).first()
        if not posto:
            logger.warning("posto_not_found", posto_id=posto_id)
            response = {
                "request_id": request_id,
                "status": "erro",
                "mensagem": f"O posto {posto_id} não existe no servidor {settings.SERVER_ID}"
            }
            await mqtt_client.publish(f"client/{client_id}/postos/reserva/response", response)
            return

        # 3. Verifica se já existe uma reserva ativa
        carregamento_existente = db.query(CarregamentoAtivo).filter(
            and_(
                CarregamentoAtivo.carro_id == carro.id,
                CarregamentoAtivo.ponto_carregamento_id == posto.id,
                CarregamentoAtivo.status == True
            )
        ).first()

        if carregamento_existente:
            logger.warning("posto_already_reserved", 
                         posto_id=posto_id, 
                         carro_id=carro.id)
            response = {
                "request_id": request_id,
                "status": "erro",
                "mensagem": f"O posto {posto.nome} já está reservado para este carro. Escolha outro posto."
            }
            await mqtt_client.publish(f"client/{client_id}/postos/reserva/response", response)
            return

        # 4. Cria nova reserva
        logger.info("creating_new_reservation", 
                   posto_id=posto_id, 
                   carro_id=carro.id)
        nova_reserva = CarregamentoAtivo(
            carro_id=carro.id,
            ponto_carregamento_id=posto.id,
            inicio_carregamento=datetime.now(),
            fim_carregamento=datetime.now() + timedelta(days=1),
            energia_fornecida=0.0,  # Começa com 0 pois ainda não houve carregamento
            status=True  # True indica que está ativo
        )
        db.add(nova_reserva)
        db.commit()
        logger.info("reservation_created", 
                   reserva_id=nova_reserva.id)

        response = {
            "request_id": request_id,
            "status": "sucesso",
            "mensagem": f"O posto {posto.nome} localizado no servidor {settings.SERVER_ID} foi reservado para o carro de placa {placa}."
        }
        await mqtt_client.publish(f"client/{client_id}/postos/reserva/response", response)
        logger.info("reservation_response_sent", 
                   client_id=client_id, 
                   request_id=request_id)

    except IntegrityError as e:
        db.rollback()
        logger.error("reservation_integrity_error", error=str(e), exc_info=True)
        await mqtt_client.publish(f"client/{client_id}/postos/reserva/response", {
            "request_id": request_id,
            "status": "erro",
            "mensagem": "Erro de integridade ao processar a reserva. Tente novamente."
        })
    except Exception as e:
        db.rollback()
        logger.error(f"[ERRO GERAL - handle_reserva_posto] {str(e)}", exc_info=True)
        await mqtt_client.publish(f"client/{client_id}/postos/reserva/response", {
            "request_id": request_id if 'request_id' in locals() else None,
            "status": "erro",
            "mensagem": f"Erro interno: {str(e)}"
        })
    finally:
        db.close()

def register_handlers():
    """Registra todos os handlers MQTT"""
    mqtt_client.register_handler("carros/+/status", handle_carro_status)
    mqtt_client.register_handler("carros/+/bateria", handle_carro_bateria)
    mqtt_client.register_handler("pontos/+/disponibilidade", handle_ponto_disponibilidade)
    mqtt_client.register_handler("reservas/+/status", handle_reserva_status)
    mqtt_client.register_handler("server/postos/request", handle_postos_request)
    mqtt_client.register_handler("server/postos/reserva", handle_reserva_posto)
    logger.info("handlers_registered") 