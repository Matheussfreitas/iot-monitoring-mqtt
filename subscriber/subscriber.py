import json
import sys
from datetime import datetime
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
    received_at = datetime.now()

    raw_payload = message.payload.decode()
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        print(f"Mensagem ignorada: payload não é JSON válido: {raw_payload}")
        return

    latencia_ms = None
    sent_at_str = payload.get("sent_at")
    if sent_at_str:
        try:
            sent_at = datetime.fromisoformat(sent_at_str)
            latencia_ms = round((received_at - sent_at).total_seconds() * 1000, 2)
        except ValueError:
            pass

    record = {
        **payload,
        "sent_at": sent_at_str,
        "received_at": received_at.isoformat(),
        "latencia_ms": latencia_ms,
    }
    insert_reading(record)

    latencia_info = f" | Latência: {latencia_ms} ms" if latencia_ms is not None else ""
    print(
        f"[{payload.get('timestamp')}] {payload.get('device_id')} | "
        f"Temperatura: {payload.get('temperature')} °C | Umidade: {payload.get('humidity')} %"
        f"{latencia_info}"
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
