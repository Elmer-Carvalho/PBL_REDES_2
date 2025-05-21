import os
import json
import paho.mqtt.client as mqtt
import time

mqtt_broker = os.getenv('MQTT_BROKER', 'localhost')
mqtt_port = int(os.getenv('MQTT_PORT', 1883))

class GasStationClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.response_received = False
        self.response_data = None

    def on_connect(self, client, userdata, flags, rc):
        print(f"Conectado ao broker MQTT com código: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            self.response_data = json.loads(msg.payload.decode())
            self.response_received = True
        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")

    def connect(self):
        self.client.connect(mqtt_broker, mqtt_port, 60)
        self.client.loop_start()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def get_user_input(self):
        print("\n=== Sistema de Reserva de Postos de Gasolina ===")
        
        # Seleção do servidor
        print("\nServidores disponíveis:")
        print("1 - Servidor 1")
        print("2 - Servidor 2")
        print("3 - Servidor 3")
        
        while True:
            try:
                server_id = int(input("\nA qual servidor deseja se conectar? (1-3): "))
                if 1 <= server_id <= 3:
                    break
                print("Por favor, escolha um servidor válido (1-3)")
            except ValueError:
                print("Por favor, digite um número válido")

        # Nome do cliente
        client_name = input("\nQual o seu nome? ")

        # Cidades para abastecimento
        cities = []
        while True:
            city = input("\nOnde deseja abastecer seu carro? ")
            cities.append(city)
            
            while True:
                add_more = input("\nDeseja adicionar mais um ponto de abastecimento? (S/N): ").upper()
                if add_more in ['S', 'N']:
                    break
                print("Por favor, responda com S ou N")
            
            if add_more == 'N':
                break

        return {
            'server_id': server_id,
            'client_name': client_name,
            'cities': cities
        }

    def send_request(self, data):
        self.response_received = False
        self.response_data = None
        
        # Inscrever no tópico de resposta
        self.client.subscribe(f"server/response/{data['client_name']}")
        
        # Enviar requisição
        self.client.publish(
            f"client/request/{data['server_id']}",
            json.dumps({
                'client_name': data['client_name'],
                'cities': data['cities']
            })
        )

        # Aguardar resposta
        timeout = 10  # segundos
        start_time = time.time()
        while not self.response_received and time.time() - start_time < timeout:
            time.sleep(0.1)

        if self.response_received:
            self.display_response()
        else:
            print("\nTempo limite excedido. Não foi possível obter resposta do servidor.")

    def display_response(self):
        if not self.response_data:
            return

        print("\n=== Resultado da Reserva ===")
        print(f"Cliente: {self.response_data['client_name']}")
        print(f"\nStatus: {self.response_data.get('message', 'Operação concluída')}")
        print("\nStatus dos postos:")
        
        for city, available in self.response_data['available_stations'].items():
            status = "Reservado com sucesso" if available else "Não disponível"
            print(f"- {city}: {status}")

def main():
    client = GasStationClient()
    client.connect()

    try:
        while True:
            data = client.get_user_input()
            client.send_request(data)
            
            while True:
                continue_ = input("\nDeseja fazer outra reserva? (S/N): ").upper()
                if continue_ in ['S', 'N']:
                    break
                print("Por favor, responda com S ou N")
            
            if continue_ == 'N':
                break

    finally:
        client.disconnect()

if __name__ == "__main__":
    main() 