const temperatureEl = document.getElementById("temperature");
const humidityEl = document.getElementById("humidity");
const deviceEl = document.getElementById("device");
const readingsEl = document.getElementById("readings");

async function fetchDados() {
  const res = await fetch("/api/dados");
  const readings = await res.json();

  if (readings.length === 0) return;

  const latest = readings[0];
  temperatureEl.textContent = `${latest.temperature} °C`;
  humidityEl.textContent = `${latest.humidity} %`;
  deviceEl.textContent = latest.device_id;

  readingsEl.innerHTML = "";
  readings.forEach((d) => {
    const item = document.createElement("li");
    item.textContent = `${d.timestamp} | ${d.device_id} | Temp: ${d.temperature} °C | Umidade: ${d.humidity}%`;
    readingsEl.appendChild(item);
  });
}

fetchDados();
setInterval(fetchDados, 2000);
