# Client Servidor - Interface Cliente MQTT

## Visão Geral

Este projeto representa a interface cliente do sistema de carregamento de veículos elétricos, totalmente modularizada e preparada para rodar em containers Docker. Cada instância do `client_servidor` é um cliente independente, capaz de se comunicar com os servidores via MQTT, consultar postos de carregamento e exibir os resultados ao usuário.

## Como Funciona a Comunicação

- **Protocolo:** MQTT (via broker Mosquitto)
- **Fluxo:**
  1. O cliente publica uma solicitação de consulta de postos no tópico `server/postos/request`.
  2. Os servidores escutam esse tópico, processam a solicitação e publicam a resposta no tópico `client/postos/response`.
  3. O cliente recebe a resposta e exibe os dados ao usuário via API HTTP (FastAPI).

## Estrutura do Projeto

```
client_servidor/
├── app/
│   ├── main.py                # FastAPI: endpoint /postos para consulta
│   ├── services/
│   │   └── mqtt_service.py    # Serviço de comunicação MQTT
│   └── core/
│       └── config.py          # Configurações de broker, porta, etc
├── Dockerfile                 # Dockerfile pronto para build
├── requirements.txt           # Dependências do projeto
├── README.md                  # Este arquivo
```

## Como Rodar com Docker Compose

O client_servidor é orquestrado pelo `docker-compose.yml` na raiz do projeto, junto com o broker e os servidores.

### Subindo o sistema completo

Na raiz do projeto, execute:
```sh
docker-compose up --build
```

Isso irá subir:
- O broker Mosquitto (serviço central MQTT)
- O servidor principal (server_1)
- Dois clientes (`client_servidor_1` e `client_servidor_2`), cada um em um container independente

### Acessando os clientes

- Cliente 1: [http://localhost:8001/docs](http://localhost:8001/docs)
- Cliente 2: [http://localhost:8002/docs](http://localhost:8002/docs)

Você pode testar o endpoint `/postos` diretamente pela interface Swagger do FastAPI.

## Como funciona a comunicação do cliente

- Cada container do `client_servidor` é um cliente MQTT independente, identificado por um `CLIENT_ID` único.
- Ao acessar `/postos`, o client publica uma mensagem MQTT solicitando os postos cadastrados.
- Os servidores respondem via MQTT, e o client retorna a resposta para o usuário.
- Toda a comunicação MQTT é feita via broker Mosquitto, compartilhado entre todos os containers.

## Como adicionar novos clientes

Para adicionar mais clientes, basta duplicar o bloco do serviço no `docker-compose.yml`, mudando o nome, a porta e o `MQTT_CLIENT_ID`. Exemplo:

```yaml
client_servidor_3:
  build: ./client_servidor
  container_name: client_servidor_3
  environment:
    - MQTT_BROKER=broker
    - MQTT_PORT=1883
    - MQTT_CLIENT_ID=cliente3
  ports:
    - "8003:8001"
  depends_on:
    - broker
  networks:
    - carregamento_network
```

Depois, rode novamente:
```sh
docker-compose up --build
```

Acesse o novo cliente em: [http://localhost:8003/docs](http://localhost:8003/docs)

## O que é possível fazer no client_servidor

- Consultar postos de carregamento disponíveis nos servidores via MQTT
- Testar múltiplos clientes simultâneos, cada um em um container independente
- Integrar facilmente com novos servidores ou expandir a quantidade de clientes
- Usar a interface Swagger do FastAPI para testar endpoints

## Observações

- O client_servidor depende do broker Mosquitto estar rodando e acessível na rede Docker.
- O sistema é totalmente escalável: basta adicionar mais clientes ou servidores conforme necessário.
- Toda a comunicação entre clientes e servidores é feita via MQTT, garantindo modularidade e desacoplamento.

---