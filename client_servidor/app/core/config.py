import os

MQTT_BROKER = os.getenv("MQTT_BROKER", "broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "client_servidor") 