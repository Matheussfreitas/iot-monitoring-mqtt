"""
Load test — spawns N simultaneous MQTT publishers and reports results.

Usage:
    python publisher/load_test.py --n-clientes 5 --duracao 30 --intervalo 1
"""

import argparse
import json
import random
import sys
import time
import threading
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import paho.mqtt.client as mqtt

MQTT_TOPIC = "iot/sala/dados"

parser = argparse.ArgumentParser(description="Load test MQTT — múltiplos publishers simultâneos")
parser.add_argument("--n-clientes", type=int, default=5, help="Número de publishers simultâneos")
parser.add_argument("--duracao", type=float, default=30.0, help="Duração do teste em segundos")
parser.add_argument("--intervalo", type=float, default=1.0, help="Intervalo entre publicações (s)")
parser.add_argument("--broker", default="localhost")
parser.add_argument("--port", type=int, default=1883)
args = parser.parse_args()


def run_client(device_id: str, stats: dict, stop_event: threading.Event):
    sent = 0
    errors = 0
    start = time.monotonic()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(args.broker, args.port)
        client.loop_start()

        while not stop_event.is_set():
            payload = {
                "device_id": device_id,
                "temperature": round(random.uniform(20, 30), 2),
                "humidity": round(random.uniform(45, 75), 2),
                "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                "sent_at": datetime.now().isoformat(),
            }
            try:
                result = client.publish(MQTT_TOPIC, json.dumps(payload))
                result.wait_for_publish()
                sent += 1
            except Exception:
                errors += 1

            time.sleep(args.intervalo)
    except Exception as e:
        errors += 1
        print(f"[{device_id}] Erro de conexão: {e}")
    finally:
        client.loop_stop()
        client.disconnect()

    elapsed = time.monotonic() - start
    stats[device_id] = {
        "enviadas": sent,
        "erros": errors,
        "duracao_s": round(elapsed, 1),
        "taxa_msg_s": round(sent / elapsed, 2) if elapsed > 0 else 0,
    }


def print_report(stats: dict):
    print("\n" + "=" * 62)
    print(f"{'SENSOR':<22} {'ENVIADAS':>9} {'ERROS':>7} {'DURAÇÃO':>9} {'MSG/S':>8}")
    print("-" * 62)
    total_sent = total_errors = 0
    for device_id, s in sorted(stats.items()):
        print(
            f"{device_id:<22} {s['enviadas']:>9} {s['erros']:>7}"
            f" {s['duracao_s']:>8.1f}s {s['taxa_msg_s']:>8.2f}"
        )
        total_sent += s["enviadas"]
        total_errors += s["erros"]
    print("-" * 62)
    print(f"{'TOTAL':<22} {total_sent:>9} {total_errors:>7}")
    print("=" * 62)


def main():
    n = args.n_clientes
    print(f"Iniciando load test: {n} clientes | {args.duracao}s | intervalo {args.intervalo}s")
    print(f"Broker: {args.broker}:{args.port}\n")

    stop_event = threading.Event()
    stats: dict = {}
    threads = []

    for i in range(1, n + 1):
        device_id = f"sensor-test-{i:02d}"
        t = threading.Thread(
            target=run_client,
            args=(device_id, stats, stop_event),
            daemon=True,
        )
        threads.append(t)
        t.start()

    try:
        time.sleep(args.duracao)
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
    finally:
        stop_event.set()
        for t in threads:
            t.join(timeout=5)

    print_report(stats)


if __name__ == "__main__":
    main()
