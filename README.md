# IoT Monitoring MQTT

Projeto simples de monitoramento IoT com MQTT. O repositório contém um broker Mosquitto em Docker, scripts Python para publicar e consumir mensagens MQTT e um dashboard Flask que recebe dados do broker e atualiza a interface em tempo real com Socket.IO.

## Mapa dos arquivos

```text
.
├── dashboard/
│   └── app.py                 # Servidor Flask + Socket.IO que assina o tópico do dashboard
├── mosquitto/
│   └── config/
│       └── mosquitto.conf     # Configuração do broker MQTT
├── publisher/
│   └── publisher.py           # Publicador de temperatura de exemplo
├── subscriber/
│   └── subscriber.py          # Consumidor de temperatura de exemplo
├── templates/
│   ├── index.html             # Tela do dashboard
│   ├── script.js              # Cliente Socket.IO do dashboard
│   └── style.css              # Estilos da tela
├── docker-compose.yml         # Sobe o broker Mosquitto na porta 1883
├── requirements.txt           # Dependências Python do projeto
└── LICENSE
```

## Requisitos

- Python 3.10 ou superior
- Docker e Docker Compose

## Configuração

Crie e ative um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Suba o broker MQTT:

```bash
docker compose up -d
```

O Mosquitto ficará disponível em `localhost:1883`.

## Executando o exemplo simples

Em um terminal, inicie o subscriber:

```bash
python subscriber/subscriber.py
```

Em outro terminal, inicie o publisher:

```bash
python publisher/publisher.py
```

Esse fluxo usa o tópico `casa/sala/temperatura` e envia apenas um valor numérico de temperatura a cada 2 segundos.

## Executando o dashboard

Inicie o servidor web:

```bash
python dashboard/app.py
```

Acesse:

```text
http://localhost:5000
```

O dashboard assina o tópico `iot/sala/dados` e espera mensagens JSON neste formato:

```json
{
  "device_id": "sensor-sala-01",
  "temperature": 24.8,
  "humidity": 61,
  "timestamp": "2026-06-14 10:30:00"
}
```

Para testar o dashboard manualmente, publique uma mensagem nesse tópico usando qualquer cliente MQTT conectado em `localhost:1883`.

## Tópicos MQTT usados

| Tópico | Usado por | Payload esperado |
| --- | --- | --- |
| `casa/sala/temperatura` | `publisher.py` e `subscriber.py` | Número com a temperatura |
| `iot/sala/dados` | `dashboard/app.py` | JSON com `device_id`, `temperature`, `humidity` e `timestamp` |

## Encerrando

Para parar o broker:

```bash
docker compose down
```
