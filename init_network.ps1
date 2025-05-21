# Criar a rede se não existir
docker network create gas-station-network -d bridge
Write-Host "Rede 'gas-station-network' criada com sucesso!" 