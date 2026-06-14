import paho.mqtt.client as mqtt
import time
import random

broker = "localhost"
topico = "casa/sala/temperatura"
client = mqtt.Client()
client.connect(broker)

while True:
  temperatura = round(random.uniform(20, 30), 2)
  client.publish(topico, temperatura)
  print(f"Temperatura enviada: {temperatura}°C")
  time.sleep(2)