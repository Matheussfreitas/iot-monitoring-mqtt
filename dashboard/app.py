import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template, request

from database.db import get_config, get_latest_readings, get_latencia_stats, get_sensores

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_CONTROL_TOPIC = "iot/sala/controle"

BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "templates"),
    static_url_path="/static",
)

if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_start()


def publish_command(payload: dict):
    mqtt_client.publish(MQTT_CONTROL_TOPIC, json.dumps(payload))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/dados")
def dados():
    device_id = request.args.get("device_id")
    return jsonify(get_latest_readings(limit=10, device_id=device_id))


@app.route("/api/sensores")
def sensores():
    return jsonify(get_sensores())


@app.route("/api/latencia")
def latencia():
    return jsonify(get_latencia_stats())


@app.route("/api/config")
def config_get():
    device_id = request.args.get("device_id", "sensor-sala-01")
    return jsonify(get_config(device_id))


@app.route("/api/comandos", methods=["POST"])
def comandos():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"erro": "Body JSON inválido"}), 400

    allowed = {
        "device_id", "intervalo", "pausado",
        "temp_min", "temp_max", "humidity_min", "humidity_max",
        "falha_prob", "falha_duracao_max",
    }
    command = {k: v for k, v in body.items() if k in allowed}
    if not command:
        return jsonify({"erro": "Nenhum campo válido no comando"}), 400

    publish_command(command)
    return jsonify({"ok": True, "comando": command})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
