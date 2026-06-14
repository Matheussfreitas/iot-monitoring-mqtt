import paho.mqtt.client as mqtt

broker = "localhost"
topico = "casa/sala/temperatura"

def on_message(client, userdata, message):
  print(f"Temperatura recebida: {message.payload.decode()}°C")

client = mqtt.Client()
client.connect(broker)
client.subscribe(topico)
client.on_message = on_message
client.loop_forever() 