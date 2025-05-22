# Sistema Distribuído de Gerenciamento de Postos de Carregamento

## Visão Geral

Este projeto implementa uma arquitetura distribuída para gerenciamento de postos de carregamento de veículos elétricos, utilizando microserviços em containers Docker, comunicação via MQTT e APIs HTTP (FastAPI) para integração com clientes.

A solução é composta por:
- **Múltiplos servidores** (ex: `server_1`, `server_2`), cada um com seu próprio banco de dados isolado.
- **Múltiplos clientes** (ex: `client_servidor_1`, `client_servidor_2`), que interagem via HTTP e MQTT.
- **Um broker MQTT** (Mosquitto) para comunicação assíncrona entre clientes e servidores.

---

## Arquitetura do Projeto

```
+-------------------+         +-------------------+         +-------------------+
|                   |         |                   |         |                   |
|  client_servidor  | <-----> |   broker MQTT     | <-----> |     server_X      |
|   (FastAPI+MQTT)  |         |   (Mosquitto)     |         | (FastAPI+MQTT+DB) |
+-------------------+         +-------------------+         +-------------------+
```

- **Clientes**: expõem APIs HTTP para usuários/sistemas externos e publicam comandos via MQTT.
- **Broker**: roteia mensagens MQTT entre clientes e servidores.
- **Servidores**: processam comandos, mantêm bancos de dados isolados e respondem via MQTT.

---

## Componentes

### 1. Broker MQTT
- **Função:** Roteia mensagens entre clientes e servidores.
- **Imagem:** `eclipse-mosquitto`
- **Portas:** 1883 (MQTT), 9001 (WebSocket)
- **Configuração:** Definida em `mosquitto.conf` e volumes para persistência de dados e logs.

### 2. Servidores (`server_1`, `server_2`, ...)
- **Função:** Gerenciam postos e reservas, cada um com seu próprio banco de dados.
- **Tecnologia:** Python, FastAPI, SQLAlchemy, SQLite, gmqtt, structlog.
- **Banco de Dados:** Cada servidor possui um arquivo `.db` próprio, isolado por volume Docker.
- **Comunicação:**
  - Recebem comandos via MQTT (ex: reservas, atualizações de status).
  - Respondem via MQTT para tópicos específicos do cliente.
- **Isolamento:** Cada servidor só processa mensagens MQTT destinadas ao seu próprio `server_id`.

#### Principais Handlers MQTT:
- `server/postos/request`: Consulta de postos disponíveis.
- `server/postos/reserva`: Processamento de reservas de postos.
- Outros handlers para status de carros, baterias, etc.

#### Isolamento de Dados:
- Cada servidor monta seu próprio volume de dados (`./server/Server_X/data:/app/data`).
- O banco de dados é definido por `DATABASE_URL=sqlite:///./data/serverX.db`.
- O handler de reserva só processa mensagens com `server_id` igual ao do servidor.

### 3. Clientes (`client_servidor_1`, `client_servidor_2`, ...)
- **Função:** Interface HTTP (FastAPI) para usuários finais ou sistemas externos.
- **Tecnologia:** Python, FastAPI, gmqtt.
- **Comunicação:**
  - Recebem requisições HTTP (ex: `/postos`, `/reservar`).
  - Publicam comandos via MQTT para os servidores.
  - Aguardam respostas via MQTT e retornam para o usuário HTTP.

#### Principais Endpoints HTTP:
- `GET /postos?server_id=server1`: Lista postos do servidor especificado.
- `POST /reservar`: Envia uma requisição de reserva para o servidor desejado.

---

## Fluxo de Comunicação

1. **Cliente recebe requisição HTTP** (ex: POST `/reservar`).
2. **Cliente publica mensagem MQTT** no tópico `server/postos/reserva` com o payload e o `server_id` de destino.
3. **Todos os servidores recebem a mensagem**, mas **apenas o servidor com o `server_id` correspondente processa**.
4. **Servidor processa a reserva** (valida carro, posto, disponibilidade, etc).
5. **Servidor responde via MQTT** no tópico exclusivo do cliente (ex: `client/cliente1/postos/reserva/response`).
6. **Cliente recebe a resposta MQTT** e retorna o resultado via HTTP para o usuário.

---

## Como criar novos clientes

1. **Copie a pasta do cliente** (ex: `client_servidor`).
2. **Altere o nome do container e as portas** no `docker-compose.yml`:
   ```yaml
   client_servidor_3:
     build: ./client_servidor
     container_name: client_servidor_3
     environment:
       - MQTT_BROKER=broker
       - MQTT_PORT=1883
       - MQTT_CLIENT_ID=cliente3
     ports:
       - "8004:8001"
     depends_on:
       - broker
     networks:
       - carregamento_network
   ```
3. **Altere o `MQTT_CLIENT_ID`** no `.env` ou nas variáveis de ambiente do novo cliente.
4. **Suba o novo cliente**:
   ```bash
   docker-compose up --build
   ```
5. **Acesse a interface HTTP** do novo cliente (ex: `http://localhost:8004/docs`).

---

## Como criar novos servidores

1. **Copie a pasta do servidor** (ex: `Server_3`).
2. **Altere o nome do container, variáveis e volumes** no `docker-compose.yml`:
   ```yaml
   server_3:
     build: ./server/Server_3
     container_name: server_3
     environment:
       - DATABASE_URL=sqlite:///./data/server3.db
       - MQTT_BROKER=broker
       - MQTT_PORT=1883
       - SERVER_ID=server3
     ports:
       - "8005:8000"
     volumes:
       - ./server/Server_3/app:/app/app
       - ./server/Server_3/data:/app/data
     depends_on:
       - broker
     networks:
       - carregamento_network
   ```
3. **Garanta que o `SERVER_ID`** no `.env` ou nas variáveis de ambiente está correto.
4. **Suba o novo servidor**:
   ```bash
   docker-compose up --build
   ```
5. **Acesse a API HTTP** do novo servidor (ex: `http://localhost:8005`).

---

## Como subir o sistema do zero

1. **Remova volumes antigos (opcional, mas recomendado):**
   ```bash
   docker-compose down -v
   ```
2. **Suba todos os serviços:**
   ```bash
   docker-compose up --build
   ```
3. **Acesse as interfaces HTTP dos clientes e servidores conforme as portas configuradas.**
4. **Use o Swagger (`/docs`) dos clientes para testar reservas e consultas.**

---

## Como validar o isolamento dos bancos

- Crie uma reserva via `client_servidor_1` para o `server_1`.
- Consulte o banco de dados do `server_2` — ele não deve ter a reserva criada no `server_1`.
- Cada servidor só terá os dados das operações destinadas a ele.

---

## Exemplo de payload de reserva

```json
{
  "placa": "ABC1234",
  "modelo": "BYD Dolphin",
  "capacidade_bateria": 44.5,
  "nivel_bateria_atual": 22.3,
  "taxa_descarga": 0.19,
  "posto_id": 5,
  "server_id": "server1"
}
```

---

## Dúvidas Frequentes

- **Posso rodar vários clientes e servidores ao mesmo tempo?**
  Sim! Basta garantir que cada um tenha seu próprio `MQTT_CLIENT_ID` (cliente) ou `SERVER_ID` (servidor) e volumes de dados separados.

- **Como monitorar logs?**
  Use `docker-compose logs -f server_1` ou `server_2` ou qualquer outro serviço.

- **Como garantir que cada servidor só processe suas mensagens?**
  O handler de reserva só processa mensagens com `server_id` igual ao do servidor.

---

## Conclusão

O sistema foi projetado para ser **modular, escalável, seguro e fácil de manter**.  
A comunicação assíncrona via MQTT permite desacoplamento total entre clientes e servidores, e o isolamento de dados é garantido por volumes Docker e lógica de aplicação.

Se precisar de exemplos de comandos, scripts de inicialização, ou quiser expandir a arquitetura, basta pedir! 