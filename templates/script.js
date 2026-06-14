const socket = io();

const temperatureEl = document.getElementById("temperature");
const humidityEl = document.getElementById("humidity");
const deviceEl = document.getElementById("device");
const readingsEl = document.getElementById("readings");

socket.on("mqtt_data", (data) => {
  temperatureEl.textContent = `${data.temperature} °C`;
  humidityEl.textContent = `${data.humidity} %`;
  deviceEl.textContent = data.device_id;

  const item = document.createElement("li");
  item.textContent = `${data.timestamp} | ${data.device_id} | Temp: ${data.temperature} °C | Umidade: ${data.humidity}%`;

  readingsEl.prepend(item);

  if (readingsEl.children.length > 10) {
    readingsEl.removeChild(readingsEl.lastChild);
  }
});