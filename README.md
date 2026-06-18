# IoT Monitoring MQTT

Projeto simples de monitoramento IoT com MQTT. O fluxo principal sobe um broker Mosquitto, executa um publisher Python que simula um sensor de sala e mostra as leituras em um dashboard Flask atualizado em tempo real com Socket.IO.

## Mapa dos arquivos

```text
.
├── dashboard/
│   └── app.py                 # Servidor Flask + Socket.IO que assina o tópico do dashboard
├── mosquitto/
│   └── config/
│       └── mosquitto.conf     # Configuração do broker MQTT
├── publisher/
│   └── publisher.py           # Simula o sensor e publica os dados consumidos pelo dashboard
├── subscriber/
│   └── subscriber.py          # Monitora no terminal os mesmos dados recebidos pelo dashboard
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

## Executando a aplicação

Inicie o servidor web:

```bash
python dashboard/app.py
```

Acesse o dashboard:

```text
http://localhost:5000
```

Em outro terminal, inicie o publisher:

```bash
python publisher/publisher.py
```

O publisher publica uma nova leitura a cada 2 segundos no tópico `iot/sala/dados`. O `dashboard/app.py` assina esse mesmo tópico, recebe o JSON publicado e envia os dados para o navegador pelo evento Socket.IO `mqtt_data`.

Opcionalmente, em um terceiro terminal, rode o subscriber para acompanhar as mesmas mensagens pelo terminal:

```bash
python subscriber/subscriber.py
```

O subscriber também assina `iot/sala/dados`, decodifica o JSON e imprime uma linha resumida com horário, sensor, temperatura e umidade. Ele é útil para validar se o broker está recebendo as mensagens mesmo sem olhar o dashboard.

## Payload MQTT

Cada mensagem publicada pelo sensor simulado segue este formato:

```json
{
  "device_id": "sensor-sala-01",
  "temperature": 24.8,
  "humidity": 61.5,
  "timestamp": "2026-06-15 10:30:00"
}
```

Campos usados pelo dashboard:

- `device_id`: identificação do sensor exibida na tela.
- `temperature`: temperatura atual em graus Celsius.
- `humidity`: umidade atual em porcentagem.
- `timestamp`: data e hora da leitura exibida no histórico.

## Fluxo dos dados

1. `publisher/publisher.py` monta o JSON do sensor.
2. O publisher envia a mensagem para o Mosquitto em `localhost:1883`.
3. `dashboard/app.py` está inscrito em `iot/sala/dados` para atualizar a interface.
4. `subscriber/subscriber.py` também pode assinar `iot/sala/dados` para monitorar as mensagens no terminal.
5. Ao receber a mensagem MQTT, o dashboard decodifica o JSON.
6. O Flask-SocketIO emite o evento `mqtt_data` para a página aberta.
7. `templates/script.js` atualiza temperatura, umidade, dispositivo e histórico.

## Tópico MQTT principal

| Tópico | Publicado por | Consumido por | Payload |
| --- | --- | --- | --- |
| `iot/sala/dados` | `publisher/publisher.py` | `dashboard/app.py` e `subscriber/subscriber.py` | JSON com `device_id`, `temperature`, `humidity` e `timestamp` |

O subscriber não substitui o dashboard. Ele serve como uma leitura técnica do mesmo fluxo MQTT, útil para conferir rapidamente o que está trafegando no broker.

## Encerrando

Para parar o broker:

```bash
docker compose down
```
