import json
from pathlib import Path

import paho.mqtt.client as mqtt
from flask import Flask, render_template
from flask_socketio import SocketIO

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/sala/dados"

BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "templates"),
)
socketio = SocketIO(app, cors_allowed_origins="*")

def on_message(client, userdata, message):
    data = json.loads(message.payload.decode())
    socketio.emit("mqtt_data", data)

mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.subscribe(MQTT_TOPIC)
mqtt_client.loop_start()

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
