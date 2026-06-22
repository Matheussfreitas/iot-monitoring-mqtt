import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import paho.mqtt.client as mqtt

from database.db import init_db, insert_reading

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/sala/dados"


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Conectado ao broker MQTT em {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        print(f"Aguardando mensagens no tópico {MQTT_TOPIC}...")
    else:
        print(f"Falha ao conectar ao broker MQTT. Código: {reason_code}")


def on_message(client, userdata, message):
    raw_payload = message.payload.decode()

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        print(f"Mensagem ignorada: payload não é JSON válido: {raw_payload}")
        return

    insert_reading(payload)

    print(
        f"[{payload.get('timestamp')}] {payload.get('device_id')} | "
        f"Temperatura: {payload.get('temperature')} °C | Umidade: {payload.get('humidity')} %"
    )


init_db()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_forever()
except KeyboardInterrupt:
    print("Subscriber encerrado.")
finally:
    client.disconnect()
