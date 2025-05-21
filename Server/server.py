import os
import json
import sqlite3
from fastapi import FastAPI, HTTPException
import uvicorn
import paho.mqtt.client as mqtt
from typing import List, Dict
import requests
from contextlib import contextmanager
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()
server_id = int(os.getenv('SERVER_ID', 1))
mqtt_broker = os.getenv('MQTT_BROKER', 'localhost')
mqtt_port = int(os.getenv('MQTT_PORT', 1883))
api_port = int(os.getenv('API_PORT', 8001))

logger.info(f"Iniciando servidor {server_id} na porta {api_port}")

# Configuração do banco de dados
def init_db():
    os.makedirs('data', exist_ok=True)
    db_path = f'data/gas_stations_server_{server_id}.db'
    logger.info(f"Inicializando banco de dados em {db_path}")
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gas_stations
                 (id INTEGER PRIMARY KEY, name TEXT, city TEXT, state TEXT, is_available BOOLEAN)''')
    conn.commit()
    conn.close()
    
    # Verificar dados iniciais
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM gas_stations WHERE is_available = 1")
    count = c.fetchone()[0]
    logger.info(f"Banco de dados inicializado com {count} postos disponíveis")
    conn.close()

@contextmanager
def get_db_connection():
    db_path = f'data/gas_stations_server_{server_id}.db'
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()

# Configuração MQTT
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    logger.info(f"Conectado ao broker MQTT com código: {rc}")
    client.subscribe(f"client/request/{server_id}")
    logger.info(f"Inscrito no tópico: client/request/{server_id}")

def check_and_reserve_stations(cities: List[str], conn) -> Dict[str, bool]:
    available_stations = {}
    try:
        for city in cities:
            logger.info(f"Verificando disponibilidade para {city}")
            conn.execute("SELECT is_available FROM gas_stations WHERE city = ?", (city,))
            result = conn.fetchone()
            if result and result[0]:
                available_stations[city] = True
                conn.execute("UPDATE gas_stations SET is_available = 0 WHERE city = ?", (city,))
                logger.info(f"Posto em {city} reservado com sucesso")
            else:
                available_stations[city] = False
                logger.warning(f"Posto em {city} não está disponível")
        return available_stations
    except Exception as e:
        logger.error(f"Erro ao verificar disponibilidade: {e}")
        return {city: False for city in cities}

def check_other_servers_availability(cities: List[str]) -> Dict[str, bool]:
    available_stations = {}
    other_servers = [8001, 8002, 8003]
    other_servers.remove(api_port)
    
    for server_port in other_servers:
        try:
            logger.info(f"Verificando disponibilidade no servidor {server_port}")
            response = requests.post(
                f"http://server{server_port}:{server_port}/check_availability",
                json={"cities": cities},
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                available_stations.update(result)
                logger.info(f"Resposta do servidor {server_port}: {result}")
            else:
                logger.error(f"Erro na resposta do servidor {server_port}: {response.status_code}")
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            logger.error(f"Erro ao verificar servidor {server_port}: {e}")
            return {city: False for city in cities}
    
    return available_stations

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        client_name = data['client_name']
        cities = data['cities']
        
        logger.info(f"Recebida mensagem do cliente {client_name} para cidades: {cities}")
        
        with get_db_connection() as conn:
            # Iniciar transação
            conn.execute("BEGIN TRANSACTION")
            
            # Verificar disponibilidade local
            local_availability = check_and_reserve_stations(cities, conn)
            logger.info(f"Disponibilidade local: {local_availability}")
            
            # Verificar em outros servidores
            unavailable_cities = [city for city in cities if not local_availability.get(city, False)]
            if unavailable_cities:
                logger.info(f"Verificando disponibilidade em outros servidores para: {unavailable_cities}")
                other_servers_availability = check_other_servers_availability(unavailable_cities)
                
                # Se algum posto não estiver disponível, cancelar todas as reservas
                if not all(other_servers_availability.values()):
                    conn.rollback()
                    logger.warning("Operação cancelada: Nem todos os postos estão disponíveis")
                    response = {
                        'client_name': client_name,
                        'available_stations': {city: False for city in cities},
                        'message': "Operação cancelada: Nem todos os postos estão disponíveis"
                    }
                else:
                    local_availability.update(other_servers_availability)
                    conn.commit()
                    logger.info("Reserva realizada com sucesso")
                    response = {
                        'client_name': client_name,
                        'available_stations': local_availability,
                        'message': "Reserva realizada com sucesso"
                    }
            else:
                conn.commit()
                logger.info("Reserva realizada com sucesso (apenas local)")
                response = {
                    'client_name': client_name,
                    'available_stations': local_availability,
                    'message': "Reserva realizada com sucesso"
                }
            
            mqtt_client.publish(f"server/response/{client_name}", json.dumps(response))
            logger.info(f"Resposta enviada para o cliente {client_name}")
            
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        try:
            response = {
                'client_name': client_name,
                'available_stations': {city: False for city in cities},
                'message': f"Erro ao processar requisição: {str(e)}"
            }
            mqtt_client.publish(f"server/response/{client_name}", json.dumps(response))
        except:
            pass

# Rotas FastAPI
@app.post("/check_availability")
async def check_availability(cities: List[str]):
    logger.info(f"Verificando disponibilidade para cidades: {cities}")
    with get_db_connection() as conn:
        available_stations = check_and_reserve_stations(cities, conn)
        if all(available_stations.values()):
            conn.commit()
            logger.info(f"Todas as cidades disponíveis: {available_stations}")
            return available_stations
        else:
            conn.rollback()
            logger.warning(f"Algumas cidades não estão disponíveis: {available_stations}")
            return {city: False for city in cities}

@app.post("/add_station")
async def add_station(name: str, city: str):
    logger.info(f"Adicionando posto: {name} em {city}")
    with get_db_connection() as conn:
        try:
            conn.execute("INSERT INTO gas_stations (name, city, state, is_available) VALUES (?, ?, ?, 1)",
                        (name, city, "SP"))
            conn.commit()
            logger.info(f"Posto {name} adicionado com sucesso")
            return {"message": "Posto adicionado com sucesso"}
        except sqlite3.IntegrityError:
            conn.rollback()
            logger.error(f"Erro ao adicionar posto: cidade {city} já possui um posto")
            raise HTTPException(status_code=400, detail="Cidade já possui um posto")

# Configuração e inicialização
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

if __name__ == "__main__":
    init_db()
    mqtt_client.connect(mqtt_broker, mqtt_port, 60)
    mqtt_client.loop_start()
    logger.info(f"Servidor {server_id} iniciado e pronto para receber requisições")
    uvicorn.run(app, host="0.0.0.0", port=api_port) 