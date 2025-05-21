param(
    [Parameter(Mandatory=$true)]
    [int]$ServerNumber
)

# Criar a rede se não existir
docker network create gas-station-network -d bridge

# Construir a imagem do servidor se necessário
docker build -t pbl-2-fim-server ./Server

# Criar diretório para o banco de dados se não existir
$dataPath = Join-Path (Get-Location) "Server\data\server$ServerNumber"
New-Item -ItemType Directory -Force -Path $dataPath

# Executar o servidor específico
docker run -it --rm `
    --name "server$ServerNumber" `
    --network gas-station-network `
    -e "SERVER_ID=$ServerNumber" `
    -e "MQTT_BROKER=mosquitto" `
    -e "MQTT_PORT=1883" `
    -e "API_PORT=800$ServerNumber" `
    -p "800$ServerNumber:800$ServerNumber" `
    -v "${dataPath}:/app/data" `
    pbl-2-fim-server python server.py 