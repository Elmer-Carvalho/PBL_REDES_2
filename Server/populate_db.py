import sqlite3
import os
import sys

# Criar diretório para os bancos de dados se não existir
os.makedirs('data', exist_ok=True)

# Lista de capitais e cidades com mais de 300 mil habitantes
cities = [
    # Região Norte
    {"name": "Posto Norte Manaus", "city": "Manaus", "state": "AM"},
    {"name": "Posto Norte Belém", "city": "Belém", "state": "PA"},
    {"name": "Posto Norte Porto Velho", "city": "Porto Velho", "state": "RO"},
    {"name": "Posto Norte Rio Branco", "city": "Rio Branco", "state": "AC"},
    {"name": "Posto Norte Boa Vista", "city": "Boa Vista", "state": "RR"},
    {"name": "Posto Norte Palmas", "city": "Palmas", "state": "TO"},
    {"name": "Posto Norte Macapá", "city": "Macapá", "state": "AP"},
    
    # Região Nordeste
    {"name": "Posto Nordeste Salvador", "city": "Salvador", "state": "BA"},
    {"name": "Posto Nordeste Recife", "city": "Recife", "state": "PE"},
    {"name": "Posto Nordeste Fortaleza", "city": "Fortaleza", "state": "CE"},
    {"name": "Posto Nordeste Natal", "city": "Natal", "state": "RN"},
    {"name": "Posto Nordeste João Pessoa", "city": "João Pessoa", "state": "PB"},
    {"name": "Posto Nordeste Maceió", "city": "Maceió", "state": "AL"},
    {"name": "Posto Nordeste Aracaju", "city": "Aracaju", "state": "SE"},
    {"name": "Posto Nordeste Teresina", "city": "Teresina", "state": "PI"},
    {"name": "Posto Nordeste São Luís", "city": "São Luís", "state": "MA"},
    {"name": "Posto Nordeste Feira de Santana", "city": "Feira de Santana", "state": "BA"},
    {"name": "Posto Nordeste Campina Grande", "city": "Campina Grande", "state": "PB"},
    {"name": "Posto Nordeste Petrópolis", "city": "Petrópolis", "state": "RJ"},
    
    # Região Centro-Oeste
    {"name": "Posto Centro-Oeste Brasília", "city": "Brasília", "state": "DF"},
    {"name": "Posto Centro-Oeste Goiânia", "city": "Goiânia", "state": "GO"},
    {"name": "Posto Centro-Oeste Cuiabá", "city": "Cuiabá", "state": "MT"},
    {"name": "Posto Centro-Oeste Campo Grande", "city": "Campo Grande", "state": "MS"},
    {"name": "Posto Centro-Oeste Anápolis", "city": "Anápolis", "state": "GO"},
    
    # Região Sudeste
    {"name": "Posto Sudeste São Paulo", "city": "São Paulo", "state": "SP"},
    {"name": "Posto Sudeste Rio de Janeiro", "city": "Rio de Janeiro", "state": "RJ"},
    {"name": "Posto Sudeste Belo Horizonte", "city": "Belo Horizonte", "state": "MG"},
    {"name": "Posto Sudeste Vitória", "city": "Vitória", "state": "ES"},
    {"name": "Posto Sudeste Guarulhos", "city": "Guarulhos", "state": "SP"},
    {"name": "Posto Sudeste Campinas", "city": "Campinas", "state": "SP"},
    {"name": "Posto Sudeste São Gonçalo", "city": "São Gonçalo", "state": "RJ"},
    {"name": "Posto Sudeste Duque de Caxias", "city": "Duque de Caxias", "state": "RJ"},
    {"name": "Posto Sudeste Nova Iguaçu", "city": "Nova Iguaçu", "state": "RJ"},
    {"name": "Posto Sudeste São José dos Campos", "city": "São José dos Campos", "state": "SP"},
    {"name": "Posto Sudeste Ribeirão Preto", "city": "Ribeirão Preto", "state": "SP"},
    {"name": "Posto Sudeste Uberlândia", "city": "Uberlândia", "state": "MG"},
    {"name": "Posto Sudeste Contagem", "city": "Contagem", "state": "MG"},
    {"name": "Posto Sudeste Juiz de Fora", "city": "Juiz de Fora", "state": "MG"},
    
    # Região Sul
    {"name": "Posto Sul Curitiba", "city": "Curitiba", "state": "PR"},
    {"name": "Posto Sul Porto Alegre", "city": "Porto Alegre", "state": "RS"},
    {"name": "Posto Sul Florianópolis", "city": "Florianópolis", "state": "SC"},
    {"name": "Posto Sul Londrina", "city": "Londrina", "state": "PR"},
    {"name": "Posto Sul Joinville", "city": "Joinville", "state": "SC"},
    {"name": "Posto Sul Caxias do Sul", "city": "Caxias do Sul", "state": "RS"},
    {"name": "Posto Sul Pelotas", "city": "Pelotas", "state": "RS"},
    {"name": "Posto Sul Canoas", "city": "Canoas", "state": "RS"},
    {"name": "Posto Sul Ponta Grossa", "city": "Ponta Grossa", "state": "PR"}
]

def init_db(server_id):
    db_path = f'data/gas_stations_server_{server_id}.db'
    print(f"\nInicializando banco de dados para servidor {server_id} em {db_path}")
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Criar tabela
    c.execute('''CREATE TABLE IF NOT EXISTS gas_stations
                 (id INTEGER PRIMARY KEY, name TEXT, city TEXT, state TEXT, is_available BOOLEAN)''')
    conn.commit()
    
    return conn

def populate_server(server_id, cities):
    print(f"\nPopulando servidor {server_id}...")
    conn = init_db(server_id)
    c = conn.cursor()
    
    # Limpar tabela existente
    c.execute("DELETE FROM gas_stations")
    print(f"Tabela limpa para servidor {server_id}")
    
    # Inserir novos dados
    for city in cities:
        c.execute("INSERT INTO gas_stations (name, city, state, is_available) VALUES (?, ?, ?, 1)",
                 (city['name'], city['city'], city['state']))
        print(f"Inserido: {city['name']} em {city['city']}")
    
    conn.commit()
    
    # Verificar dados inseridos
    c.execute("SELECT COUNT(*) FROM gas_stations WHERE is_available = 1")
    count = c.fetchone()[0]
    print(f"Servidor {server_id}: {count} postos disponíveis")
    
    # Listar todas as cidades
    c.execute("SELECT city, is_available FROM gas_stations")
    stations = c.fetchall()
    print("\nCidades no servidor:")
    for city, available in stations:
        print(f"- {city}: {'Disponível' if available else 'Indisponível'}")
    
    conn.close()

def main():
    # Distribuir cidades entre os servidores
    total_cities = len(cities)
    cities_per_server = total_cities // 3
    
    # Servidor 1: Norte e parte do Nordeste
    server1_cities = cities[:cities_per_server]
    # Servidor 2: Centro-Oeste, Sudeste e parte do Nordeste
    server2_cities = cities[cities_per_server:cities_per_server*2]
    # Servidor 3: Sul e parte do Nordeste
    server3_cities = cities[cities_per_server*2:]
    
    print("\nDistribuição de cidades:")
    print(f"Servidor 1: {len(server1_cities)} cidades")
    print(f"Servidor 2: {len(server2_cities)} cidades")
    print(f"Servidor 3: {len(server3_cities)} cidades")
    
    # Popular cada servidor
    populate_server(1, server1_cities)
    populate_server(2, server2_cities)
    populate_server(3, server3_cities)
    
    print("\nBancos de dados populados com sucesso!")

if __name__ == "__main__":
    main() 