# Sistema de Reserva de Postos de Gasolina

Este projeto implementa um sistema distribuído de reserva de postos de gasolina utilizando MQTT para comunicação cliente-servidor e HTTP (FastAPI) para comunicação entre servidores.

## Estrutura do Projeto

- `Server/`: Contém o código dos servidores
  - `server.py`: Implementação do servidor com MQTT e FastAPI
  - `Dockerfile`: Configuração do container do servidor

- `Client/`: Contém o código do cliente
  - `client.py`: Implementação do cliente com interface interativa
  - `Dockerfile`: Configuração do container do cliente

## Requisitos

- Docker
- Docker Compose

## Como Executar

1. Clone o repositório
2. Na raiz do projeto, execute:
   ```bash
   docker-compose up --build
   ```

## Funcionalidades

### Cliente
- Interface interativa via terminal
- Seleção do servidor desejado
- Cadastro de múltiplos pontos de abastecimento
- Recebimento de confirmação de reserva

### Servidor
- Banco de dados SQLite para armazenamento de postos
- Comunicação MQTT com clientes
- Comunicação HTTP entre servidores
- Verificação de disponibilidade de postos
- Reserva automática de postos disponíveis

## Exemplo de Uso

1. O cliente seleciona um servidor (1-3)
2. Informa seu nome
3. Adiciona as cidades onde deseja abastecer
4. O sistema verifica a disponibilidade dos postos
5. Retorna o status de cada reserva solicitada

## Observações

- Cada cidade pode ter apenas um posto
- Os postos são distribuídos entre os três servidores
- A comunicação entre servidores é feita via HTTP
- A comunicação cliente-servidor é feita via MQTT 