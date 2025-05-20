# Servidor 1 - Sistema de Carregamento de Veículos Elétricos

Este é o Servidor 1 do sistema de carregamento de veículos elétricos, responsável por gerenciar pontos de recarga e coordenar com outros servidores para reservas de viagens longas.

## Estrutura do Projeto

```
server_1/
├── app/
│   ├── __init__.py
│   ├── main.py              # Ponto de entrada da aplicação
│   ├── config.py            # Configurações do servidor
│   ├── database.py          # Configuração do banco de dados
│   ├── models/              # Modelos de dados
│   │   ├── __init__.py
│   │   ├── carro.py
│   │   ├── ponto_carregamento.py
│   │   └── reserva.py
│   ├── routers/             # Rotas da API
│   │   ├── __init__.py
│   │   ├── carros.py
│   │   ├── pontos.py
│   │   └── reservas.py
│   ├── services/            # Lógica de negócio
│   │   ├── __init__.py
│   │   ├── carro_service.py
│   │   ├── ponto_service.py
│   │   └── reserva_service.py
│   └── mqtt/                # Configuração e handlers MQTT
│       ├── __init__.py
│       ├── client.py
│       └── handlers.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.8+
- Docker
- Docker Compose

## Instalação

1. Clone o repositório
2. Navegue até o diretório do servidor:
   ```bash
   cd server/Server_1
   ```
3. Construa e inicie os containers:
   ```bash
   docker-compose up --build
   ```

## Funcionamento

### Componentes Principais

1. **API REST (FastAPI)**
   - Gerencia pontos de carregamento
   - Processa reservas
   - Coordena com outros servidores
   - Porta padrão: 8000

2. **MQTT Broker**
   - Gerencia comunicação com veículos
   - Recebe dados de status dos carros
   - Envia atualizações de disponibilidade
   - Porta padrão: 1883

3. **Banco de Dados (SQLite)**
   - Armazena dados dos pontos de carregamento
   - Gerencia reservas
   - Mantém histórico de operações

### Endpoints Principais

- `GET /status`: Verifica status do servidor
- `GET /pontos`: Lista pontos de carregamento
- `POST /reservas`: Cria nova reserva
- `GET /reservas`: Lista reservas ativas

### Tópicos MQTT

- `carros/status`: Status dos veículos
- `carros/bateria`: Nível de bateria
- `pontos/disponibilidade`: Disponibilidade dos pontos
- `reservas/status`: Status das reservas

## Testando o Servidor

1. **API REST**
   - Use o Swagger UI em `http://localhost:8000/docs`
   - Ou utilize ferramentas como Postman/Insomnia

2. **MQTT**
   - Use um cliente MQTT como MQTT Explorer
   - Conecte em `localhost:1883`
   - Inscreva-se nos tópicos mencionados acima

## Logs

Os logs do servidor podem ser visualizados através do Docker:
```bash
docker-compose logs -f
``` 