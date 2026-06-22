const temperatureEl = document.getElementById("temperature");
const humidityEl = document.getElementById("humidity");
const deviceEl = document.getElementById("device");
const readingsEl = document.getElementById("readings");
const btnPausa = document.getElementById("btn-pausa");
const statusPausa = document.getElementById("status-pausa");
const intervaloEl = document.getElementById("intervalo");
const intervaloVal = document.getElementById("intervalo-val");
const falhaProbEl = document.getElementById("falha_prob");
const falhaProbVal = document.getElementById("falha-prob-val");
const sensorSelect = document.getElementById("sensor-select");

intervaloEl.addEventListener("input", () => {
  intervaloVal.textContent = `${intervaloEl.value}s`;
});

falhaProbEl.addEventListener("input", () => {
  falhaProbVal.textContent = `${Math.round(falhaProbEl.value * 100)}%`;
});

function sensorSelecionado() {
  return sensorSelect.value || null;
}

async function fetchSensores() {
  const res = await fetch("/api/sensores");
  const sensores = await res.json();
  const current = sensorSelecionado();

  sensorSelect.innerHTML = '<option value="">Todos</option>';
  sensores.forEach((s) => {
    const opt = document.createElement("option");
    opt.value = s.device_id;
    opt.textContent = s.device_id;
    if (s.device_id === current) opt.selected = true;
    sensorSelect.appendChild(opt);
  });
}

async function fetchDados() {
  const device = sensorSelecionado();
  const url = device ? `/api/dados?device_id=${encodeURIComponent(device)}` : "/api/dados";
  const res = await fetch(url);
  const readings = await res.json();

  if (readings.length === 0) return;

  const latest = readings[0];
  temperatureEl.textContent = `${latest.temperature} °C`;
  humidityEl.textContent = `${latest.humidity} %`;
  deviceEl.textContent = latest.device_id;

  readingsEl.innerHTML = "";
  readings.forEach((d) => {
    const item = document.createElement("li");
    const lat = d.latencia_ms != null ? ` | ${d.latencia_ms} ms` : "";
    item.textContent = `${d.timestamp} | ${d.device_id} | Temp: ${d.temperature} °C | Umidade: ${d.humidity}%${lat}`;
    readingsEl.appendChild(item);
  });
}

async function fetchLatencia() {
  const res = await fetch("/api/latencia");
  const stats = await res.json();
  const device = sensorSelecionado();

  const row = device ? stats.find((s) => s.device_id === device) : stats[0];
  if (!row) {
    document.getElementById("lat-min").textContent = "--";
    document.getElementById("lat-avg").textContent = "--";
    document.getElementById("lat-max").textContent = "--";
    return;
  }
  document.getElementById("lat-min").textContent = `${row.min_ms} ms`;
  document.getElementById("lat-avg").textContent = `${row.avg_ms} ms`;
  document.getElementById("lat-max").textContent = `${row.max_ms} ms`;
}

async function carregarConfig() {
  const device = sensorSelecionado() || "sensor-sala-01";
  const res = await fetch(`/api/config?device_id=${encodeURIComponent(device)}`);
  const cfg = await res.json();

  intervaloEl.value = cfg.intervalo;
  intervaloVal.textContent = `${cfg.intervalo}s`;
  document.getElementById("temp_min").value = cfg.temp_min;
  document.getElementById("temp_max").value = cfg.temp_max;
  document.getElementById("humidity_min").value = cfg.humidity_min;
  document.getElementById("humidity_max").value = cfg.humidity_max;
  falhaProbEl.value = cfg.falha_prob;
  falhaProbVal.textContent = `${Math.round(cfg.falha_prob * 100)}%`;
  document.getElementById("falha_duracao_max").value = cfg.falha_duracao_max;

  atualizarEstadoPausa(cfg.pausado);
}

function atualizarEstadoPausa(pausado) {
  if (pausado) {
    btnPausa.textContent = "Retomar";
    statusPausa.textContent = "Pausado";
    statusPausa.className = "status-pausado";
  } else {
    btnPausa.textContent = "Pausar";
    statusPausa.textContent = "Ativo";
    statusPausa.className = "status-ativo";
  }
}

async function enviarComando(campos) {
  const device = sensorSelecionado();
  const payload = device ? { device_id: device, ...campos } : campos;
  await fetch("/api/comandos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

async function togglePausa() {
  const pausado = btnPausa.textContent === "Pausar";
  await enviarComando({ pausado });
  atualizarEstadoPausa(pausado);
}

async function onSensorChange() {
  await carregarConfig();
  await fetchDados();
  await fetchLatencia();
}

async function tick() {
  await fetchDados();
  await fetchLatencia();
}

fetchSensores();
carregarConfig();
tick();
setInterval(tick, 2000);
setInterval(fetchSensores, 5000);
