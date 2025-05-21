# Server 2 - Sistema de Carregamento de Veículos Elétricos

Este é o Server 2, um servidor independente do sistema de carregamento de veículos elétricos. Possui seu próprio banco de dados, conjunto de pontos de carregamento e integra-se ao restante do sistema via MQTT e API REST (FastAPI).

- Banco de dados: SQLite (arquivo separado, não compartilhado com outros servidores)
- Pontos de carregamento: definidos em `pontos_carregamento.csv` (diferentes do Server 1)
- Comunicação: MQTT (broker Mosquitto) e HTTP (FastAPI)

Para rodar este servidor, utilize o docker-compose na raiz do projeto. 