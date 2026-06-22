# IoT Monitoring MQTT

Projeto de monitoramento IoT com MQTT. Suporta múltiplos sensores simultâneos, mede latência ponta-a-ponta, permite controle remoto de cada publisher pelo dashboard e inclui um script de load test para estressar o broker.

## Mapa dos arquivos

```text
.
├── dashboard/
│   └── app.py                 # Servidor Flask — dashboard e API REST
├── database/
│   └── db.py                  # Módulo SQLite compartilhado (leituras, config, latência)
├── data/
│   └── sensor_data.db         # Banco de dados criado automaticamente na primeira execução
├── mosquitto/
│   └── config/
│       └── mosquitto.conf     # Configuração do broker MQTT
├── publisher/
│   ├── publisher.py           # Simula um sensor, publica leituras e reage a comandos
│   └── load_test.py           # Load test — N publishers simultâneos em threads
├── subscriber/
│   └── subscriber.py          # Assina o tópico de dados, calcula latência e persiste no banco
├── templates/
│   ├── index.html             # Dashboard com selector de sensor, latência e painel de controle
│   ├── script.js              # Polling HTTP, selector de sensor e envio de comandos
│   └── style.css              # Estilos
├── docker-compose.yml         # Sobe o broker Mosquitto na porta 1883
├── requirements.txt           # Dependências Python
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

**Terminal 1 — subscriber** (persiste dados e calcula latência):

```bash
python subscriber/subscriber.py
```

**Terminal 2 — publisher(es)** (um ou mais sensores):

```bash
# sensor único (device-id padrão: sensor-sala-01)
python publisher/publisher.py

# múltiplos sensores em paralelo
python publisher/publisher.py --device-id sensor-sala-01 &
python publisher/publisher.py --device-id sensor-cozinha-01 &
python publisher/publisher.py --device-id sensor-externo-01 &
```

**Terminal 3 — dashboard**:

```bash
python dashboard/app.py
```

Acesse em `http://localhost:5000`. O browser atualiza automaticamente a cada 2 segundos.

## Múltiplos sensores

Cada instância do publisher recebe um `--device-id` único via CLI. A configuração de cada sensor é armazenada independentemente no banco. O dashboard exibe um dropdown com todos os sensores ativos e filtra leituras, latência e controles pelo sensor selecionado.

Comandos de controle enviados pelo dashboard incluem o `device_id` como destino — cada publisher ignora mensagens direcionadas a outros sensores.

## Latência

O publisher insere `sent_at` (timestamp ISO com precisão de milissegundos) em cada payload. O subscriber registra `received_at` no instante de recepção e calcula:

```
latencia_ms = (received_at − sent_at) × 1000
```

O dashboard exibe min / avg / máx de latência por sensor no card dedicado.

## Load test

Spawna N publishers simultâneos em threads e imprime um relatório ao fim:

```bash
python publisher/load_test.py --n-clientes 5 --duracao 30 --intervalo 1
```

| Argumento       | Padrão | Descrição                              |
|-----------------|--------|----------------------------------------|
| `--n-clientes`  | 5      | Número de publishers simultâneos       |
| `--duracao`     | 30     | Duração total do teste em segundos     |
| `--intervalo`   | 1      | Intervalo entre publicações por cliente|
| `--broker`      | localhost | Endereço do broker MQTT            |
| `--port`        | 1883   | Porta do broker                        |

Cada cliente usa `device_id = sensor-test-{N}`. O relatório exibe mensagens enviadas, erros e taxa msg/s por cliente.

## Controle do publisher

O painel de controle do dashboard envia comandos ao publisher via MQTT sem precisar reiniciá-lo. Quando um sensor está selecionado no dropdown, o comando é direcionado apenas a ele.

| Parâmetro          | Tipo   | Descrição                                          | Limite           |
|--------------------|--------|----------------------------------------------------|------------------|
| `intervalo`        | float  | Segundos entre cada publicação                     | 1 – 30 s         |
| `pausado`          | bool   | Pausa ou retoma o envio de mensagens               | —                |
| `temp_min`         | float  | Limite inferior da faixa de temperatura simulada   | < `temp_max`     |
| `temp_max`         | float  | Limite superior da faixa de temperatura simulada   | > `temp_min`     |
| `humidity_min`     | float  | Limite inferior da faixa de umidade simulada       | < `humidity_max` |
| `humidity_max`     | float  | Limite superior da faixa de umidade simulada       | > `humidity_min` |
| `falha_prob`       | float  | Probabilidade de simular falha de conexão por ciclo| 0.0 – 1.0        |
| `falha_duracao_max`| float  | Tempo máximo offline durante uma falha simulada    | 1 – 30 s         |

A configuração é persistida no banco por `device_id`. Ao reiniciar o publisher, ele retoma com os últimos valores gravados.

## Simulação de falhas de conexão

Quando `falha_prob > 0`, o publisher sorteia a cada ciclo de publicação se deve simular uma desconexão. Em caso positivo, desconecta do broker e aguarda um tempo aleatório entre `1s` e `falha_duracao_max` antes de reconectar. O evento é registrado no terminal do publisher.

Exemplo — sensor com 20% de chance de falha e até 10 s offline:

```bash
# via dashboard: selecionar sensor → setar falha_prob=0.2 e falha_duracao_max=10 → Aplicar

# ou via API:
curl -X POST http://localhost:5000/api/comandos \
  -H "Content-Type: application/json" \
  -d '{"device_id": "sensor-sala-01", "falha_prob": 0.2, "falha_duracao_max": 10}'
```

## Fluxo dos dados

```
[publisher] → iot/sala/dados    → [Mosquitto] → [subscriber] → SQLite
[dashboard] → iot/sala/controle → [Mosquitto] → [publisher]  (atualiza config)
[browser]   → GET /api/dados (a cada 2s) → [dashboard] → SQLite
[browser]   → POST /api/comandos → [dashboard] → iot/sala/controle
```

Leitura passo a passo:

1. `publisher.py` monta o payload com `sent_at` e publica em `iot/sala/dados`.
2. O Mosquitto recebe e repassa.
3. `subscriber.py` registra `received_at`, calcula `latencia_ms` e chama `insert_reading()`.
4. `db.py` grava no SQLite e remove registros com mais de 24 horas.
5. O browser faz `GET /api/dados?device_id=X` a cada 2 segundos.
6. `app.py` retorna as 10 últimas leituras do sensor selecionado.

## API

| Método | Rota                        | Descrição                                               |
|--------|-----------------------------|---------------------------------------------------------|
| GET    | `/`                         | Serve a interface do dashboard                          |
| GET    | `/api/dados`                | Últimas 10 leituras (todas os sensores)                 |
| GET    | `/api/dados?device_id=X`    | Últimas 10 leituras do sensor especificado              |
| GET    | `/api/sensores`             | Lista de sensores ativos com último timestamp           |
| GET    | `/api/latencia`             | Estatísticas de latência (min/avg/max) por sensor       |
| GET    | `/api/config?device_id=X`   | Configuração atual do sensor especificado               |
| POST   | `/api/comandos`             | Envia comando ao publisher (campos parciais aceitos)    |

Exemplo de corpo para `POST /api/comandos`:

```json
{ "device_id": "sensor-sala-01", "intervalo": 5, "temp_min": 15, "temp_max": 20 }
```

Omitir `device_id` envia o comando como broadcast para todos os publishers ativos.

## Tópicos MQTT

| Tópico                | Publicado por           | Consumido por              |
|-----------------------|-------------------------|----------------------------|
| `iot/sala/dados`      | `publisher/publisher.py`| `subscriber/subscriber.py` |
| `iot/sala/controle`   | `dashboard/app.py`      | `publisher/publisher.py`   |

O dashboard não assina nenhum tópico. Para leituras consulta o banco; para comandos publica no tópico de controle.

## Banco de dados

Criado automaticamente em `data/sensor_data.db` na primeira execução. Tabelas:

- **`readings`** — leituras de todos os sensores, com `sent_at`, `received_at` e `latencia_ms`. Retenção de 24 horas com limpeza automática a cada insert.
- **`publisher_config`** — configuração por `device_id` (chave primária). Persistida após cada comando recebido.

SQLite configurado com **WAL mode** para leituras concorrentes sem bloqueio de escrita.

## Encerrando

```bash
docker compose down
```
