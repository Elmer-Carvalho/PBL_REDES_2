param(
    [Parameter(Mandatory=$true)]
    [string]$ClientName
)

# Construir a imagem do cliente se necessário
docker build -t pbl-2-fim-client ./Client

# Executar o cliente
docker run -it --rm `
    --name "client_$ClientName" `
    --network gas-station-network `
    -e "MQTT_BROKER=mosquitto" `
    -e "MQTT_PORT=1883" `
    pbl-2-fim-client python client.py 