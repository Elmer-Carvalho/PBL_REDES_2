# Sistema de Gerenciamento de Postos de Carregamento de Veículos Elétricos

Este projeto implementa um sistema distribuído para gerenciamento de postos de carregamento de veículos elétricos, utilizando uma arquitetura baseada em microserviços com comunicação via REST API e MQTT.

## Tecnologias Utilizadas

- **FastAPI**: Framework web moderno e rápido para construção de APIs com Python
- **SQLAlchemy**: ORM (Object-Relational Mapping) para interação com banco de dados
- **SQLite**: Banco de dados local para armazenamento dos dados
- **MQTT**: Protocolo de mensageria para comunicação entre servidores
- **Docker**: Containerização da aplicação
- **Docker Compose**: Orquestração dos containers

## Arquitetura do Sistema

O sistema é composto por:

1. **Servidores (Server_1 e Server_2)**:

   - APIs REST para gerenciamento de postos
   - Banco de dados SQLite independente
   - Comunicação via MQTT para sincronização

2. **Broker MQTT**:

   - Eclipse Mosquitto como broker MQTT
   - Gerencia a comunicação entre servidores

3. **Clientes (client_1 e client_2)**:
   - Interfaces para interação com os servidores
   - Comunicação via REST API

## Como Iniciar a Aplicação

1. **Pré-requisitos**:

   - Docker
   - Docker Compose

2. **Iniciar os serviços**:

   ```bash
   docker-compose up -d
   ```

3. **Verificar status dos serviços**:

   ```bash
   docker-compose ps
   ```

4. **Acessar as interfaces**:
   - Server 1: http://localhost:8000/docs
   - Server 2: http://localhost:8003/docs
   - Cliente 1: http://localhost:8001
   - Cliente 2: http://localhost:8002

## Endpoints Disponíveis

### Postos de Carregamento

1. **Criar Posto** (POST `/`)

   - Cria um novo posto de carregamento
   - Parâmetros: nome, localização, potência máxima, tipo de conector, preço por kWh

2. **Listar Postos** (GET `/`)

   - Lista todos os postos cadastrados
   - Filtros opcionais: disponível, em manutenção

3. **Reservar Posto** (POST `/reservar`)
   - Realiza a reserva de um posto
   - Parâmetros: server_id, nome_posto, nome_cliente

## Comunicação MQTT

O sistema utiliza MQTT para manter a sincronização entre os servidores:

1. **Tópicos**:

   - `pontos/{id}/disponibilidade`: Atualizações de disponibilidade
   - `pontos/{id}/reserva`: Novas reservas
   - `pontos/{id}/carregamento`: Status de carregamento

2. **Mensagens**:
   - Formato JSON
   - Timestamp para controle de ordem
   - Informações específicas do evento

## Estratégias de Concorrência

Para garantir a consistência dos dados em cenários de múltiplos acessos simultâneos, implementamos:

1. **Bloqueio Pessimista (SELECT FOR UPDATE)**:

   - Bloqueia o registro durante a operação
   - Evita condições de corrida
   - Usa `skip_locked=True` para resposta imediata

2. **Transações Atômicas**:

   - Todas as operações em uma única transação
   - Rollback automático em caso de falha

3. **Tratamento de Erros**:
   - HTTP 409 para conflitos de concorrência
   - Mensagens claras sobre o estado da operação

## Decisões de Projeto

1. **Arquitetura Distribuída**:

   - Servidores independentes
   - Bancos de dados separados
   - Sincronização via MQTT

2. **Performance**:

   - FastAPI para alta performance
   - Bloqueio pessimista para concorrência
   - Respostas assíncronas

3. **Consistência**:

   - Transações atômicas
   - Notificações em tempo real
   - Validações de estado

4. **Escalabilidade**:
   - Arquitetura baseada em containers
   - Servidores independentes
   - Comunicação assíncrona

## Monitoramento e Logs

- Logs do Docker Compose
- Documentação interativa do FastAPI
- Monitoramento do broker MQTT

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Faça commit das alterações
4. Faça push para a branch
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT.
