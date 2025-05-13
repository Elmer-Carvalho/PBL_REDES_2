# Sistema de Reserva de Postos de Carregamento

Este é um sistema distribuído para gerenciamento de reservas de postos de carregamento de veículos elétricos, implementado usando FastAPI, MQTT e SQLite.

## Arquitetura

O sistema é composto por:
- API REST para comunicação com clientes
- Protocolo MQTT para comunicação entre servidores
- Banco de dados SQLite para armazenamento local
- Comunicação assíncrona entre servidores

## Requisitos

- Python 3.8+
- FastAPI
- SQLAlchemy
- Paho-MQTT
- HTTPX
- Uvicorn

## Instalação

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Configuração

1. Configure as variáveis de ambiente no arquivo `.env`:
```
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_CLIENT_ID=client_api
```

## Executando o Projeto

1. Inicie o servidor:
```bash
uvicorn main:app --reload
```

2. Acesse a documentação Swagger em:
```
http://localhost:8000/docs
```

## Endpoints

### GET /api/v1/stations
Retorna todas as estações disponíveis em todos os servidores.

### POST /api/v1/stations/reserve
Realiza a reserva de uma estação em qualquer servidor disponível.

## Estrutura do Projeto

```
client/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── api.py
│   ├── core/
│   │   ├── config.py
│   │   └── exceptions.py
│   ├── db/
│   │   └── session.py
│   ├── models/
│   │   └── station.py
│   ├── schemas/
│   │   └── station.py
│   └── services/
│       ├── mqtt_service.py
│       └── server_communication.py
├── main.py
└── requirements.txt
```

## Comunicação entre Servidores

O sistema utiliza o protocolo MQTT para comunicação entre servidores, permitindo:
- Broadcast de solicitações de reserva
- Notificação de disponibilidade de estações
- Sincronização de estado entre servidores

## Tratamento de Erros

O sistema implementa um módulo de erros customizados para:
- Estações não encontradas
- Reservas já existentes
- Erros de comunicação com servidores
- Dados de reserva inválidos 