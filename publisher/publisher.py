import argparse
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import paho.mqtt.client as mqtt

from database.db import get_config, init_db, save_config

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/sala/dados"
MQTT_CONTROL_TOPIC = "iot/sala/controle"

parser = argparse.ArgumentParser(description="Publisher MQTT de sensor simulado")
parser.add_argument("--device-id", default="sensor-sala-01", help="Identificador do sensor")
parser.add_argument("--broker", default=MQTT_BROKER)
parser.add_argument("--port", type=int, default=MQTT_PORT)
args = parser.parse_args()

DEVICE_ID = args.device_id
config = {}


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe(MQTT_CONTROL_TOPIC)
        print(f"[{DEVICE_ID}] Conectado. Aguardando comandos em {MQTT_CONTROL_TOPIC}")
    else:
        print(f"[{DEVICE_ID}] Falha ao conectar. Código: {reason_code}")


def on_message(client, userdata, message):
    try:
        updates = json.loads(message.payload.decode())
    except json.JSONDecodeError:
        return

    # ignora comandos destinados a outro sensor
    target = updates.pop("device_id", None)
    if target and target != DEVICE_ID:
        return

    allowed = {"intervalo", "pausado", "temp_min", "temp_max",
               "humidity_min", "humidity_max", "falha_prob", "falha_duracao_max"}
    updates = {k: v for k, v in updates.items() if k in allowed}

    if "intervalo" in updates:
        updates["intervalo"] = max(1.0, min(30.0, float(updates["intervalo"])))
    if "falha_prob" in updates:
        updates["falha_prob"] = max(0.0, min(1.0, float(updates["falha_prob"])))
    if "temp_min" in updates and "temp_max" in updates:
        if float(updates["temp_min"]) >= float(updates["temp_max"]):
            print(f"[{DEVICE_ID}] Comando ignorado: temp_min >= temp_max")
            return
    if "humidity_min" in updates and "humidity_max" in updates:
        if float(updates["humidity_min"]) >= float(updates["humidity_max"]):
            print(f"[{DEVICE_ID}] Comando ignorado: humidity_min >= humidity_max")
            return

    config.update(updates)
    save_config(DEVICE_ID, config)
    print(f"[{DEVICE_ID}] Config atualizada: {updates}")


def build_payload() -> dict:
    return {
        "device_id": DEVICE_ID,
        "temperature": round(random.uniform(config["temp_min"], config["temp_max"]), 2),
        "humidity": round(random.uniform(config["humidity_min"], config["humidity_max"]), 2),
        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "sent_at": datetime.now().isoformat(),
    }


def simulate_failure(client):
    prob = config.get("falha_prob", 0.0)
    if prob > 0 and random.random() < prob:
        downtime = random.uniform(1, config.get("falha_duracao_max", 5.0))
        print(f"[{DEVICE_ID}] Simulando falha de conexão por {downtime:.1f}s")
        client.disconnect()
        time.sleep(downtime)
        client.reconnect()
        time.sleep(0.5)


init_db()
config.update(get_config(DEVICE_ID))

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(args.broker, args.port)
client.loop_start()

try:
    while True:
        if config.get("pausado"):
            time.sleep(1)
            continue

        payload = build_payload()
        result = client.publish(MQTT_TOPIC, json.dumps(payload))
        result.wait_for_publish()
        print(f"[{DEVICE_ID}] Publicado: temp={payload['temperature']} hum={payload['humidity']}")

        simulate_failure(client)
        time.sleep(config["intervalo"])
except KeyboardInterrupt:
    print(f"[{DEVICE_ID}] Encerrado.")
finally:
    client.loop_stop()
    client.disconnect()
