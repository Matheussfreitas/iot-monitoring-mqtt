import json
import random
import time
from datetime import datetime

import paho.mqtt.client as mqtt


MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/sala/dados"
DEVICE_ID = "sensor-sala-01"
PUBLISH_INTERVAL_SECONDS = 2


def build_sensor_payload():
    return {
        "device_id": DEVICE_ID,
        "temperature": round(random.uniform(20, 30), 2),
        "humidity": round(random.uniform(45, 75), 2),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT)
client.loop_start()

try:
    while True:
        payload = build_sensor_payload()
        message = json.dumps(payload)

        result = client.publish(MQTT_TOPIC, message)
        result.wait_for_publish()

        print(f"Dados enviados para {MQTT_TOPIC}: {message}")
        time.sleep(PUBLISH_INTERVAL_SECONDS)
except KeyboardInterrupt:
    print("Publicador encerrado.")
finally:
    client.loop_stop()
    client.disconnect()
