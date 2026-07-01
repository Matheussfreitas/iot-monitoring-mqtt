import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sensor_data.db"

DEFAULT_CONFIG = {
    "intervalo": 2.0,
    "pausado": False,
    "temp_min": 20.0,
    "temp_max": 30.0,
    "humidity_min": 45.0,
    "humidity_max": 75.0,
    "falha_prob": 0.0,
    "falha_duracao_max": 5.0,
}


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def _migrate(conn: sqlite3.Connection):
    # readings: add latency columns if missing
    existing = {row[1] for row in conn.execute("PRAGMA table_info(readings)")}
    for col, typedef in [
        ("sent_at", "TEXT"),
        ("received_at", "TEXT"),
        ("latencia_ms", "REAL"),
    ]:
        if col not in existing:
            conn.execute(f"ALTER TABLE readings ADD COLUMN {col} {typedef}")

    # publisher_config: recreate if using old id=1 schema (no device_id column)
    cfg_cols = {row[1] for row in conn.execute("PRAGMA table_info(publisher_config)")}
    if "device_id" not in cfg_cols:
        conn.execute("DROP TABLE IF EXISTS publisher_config")
        _create_config_table(conn)


def _create_config_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS publisher_config (
            device_id        TEXT    PRIMARY KEY,
            intervalo        REAL    NOT NULL DEFAULT 2.0,
            pausado          INTEGER NOT NULL DEFAULT 0,
            temp_min         REAL    NOT NULL DEFAULT 20.0,
            temp_max         REAL    NOT NULL DEFAULT 30.0,
            humidity_min     REAL    NOT NULL DEFAULT 45.0,
            humidity_max     REAL    NOT NULL DEFAULT 75.0,
            falha_prob       REAL    NOT NULL DEFAULT 0.0,
            falha_duracao_max REAL   NOT NULL DEFAULT 5.0
        )
    """)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id   TEXT    NOT NULL,
                temperature REAL    NOT NULL,
                humidity    REAL    NOT NULL,
                timestamp   TEXT    NOT NULL,
                sent_at     TEXT,
                received_at TEXT,
                latencia_ms REAL
            )
        """)
        _create_config_table(conn)
        _migrate(conn)


def insert_reading(data: dict):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO readings"
            " (device_id, temperature, humidity, timestamp, sent_at, received_at, latencia_ms)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                data["device_id"],
                data["temperature"],
                data["humidity"],
                data["timestamp"],
                data.get("sent_at"),
                data.get("received_at"),
                data.get("latencia_ms"),
            ),
        )
        conn.execute("""
            DELETE FROM readings
            WHERE datetime(COALESCE(received_at, sent_at, timestamp)) IS NOT NULL
              AND datetime(COALESCE(received_at, sent_at, timestamp)) < datetime('now', '-24 hours')
        """)


def get_latest_readings(limit: int = 10, device_id: str = None) -> list:
    with get_connection() as conn:
        if device_id:
            rows = conn.execute(
                "SELECT device_id, temperature, humidity, timestamp, latencia_ms"
                " FROM readings WHERE device_id = ? ORDER BY id DESC LIMIT ?",
                (device_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT device_id, temperature, humidity, timestamp, latencia_ms"
                " FROM readings ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(row) for row in rows]


def get_sensores() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT r.device_id, r.timestamp as ultimo_dado"
            " FROM readings r"
            " JOIN ("
            "   SELECT device_id, MAX(id) as ultimo_id"
            "   FROM readings GROUP BY device_id"
            " ) ultimos ON ultimos.ultimo_id = r.id"
            " ORDER BY r.id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_latencia_stats() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT device_id,"
            " ROUND(MIN(latencia_ms), 2) as min_ms,"
            " ROUND(AVG(latencia_ms), 2) as avg_ms,"
            " ROUND(MAX(latencia_ms), 2) as max_ms"
            " FROM readings WHERE latencia_ms IS NOT NULL"
            " GROUP BY device_id"
        ).fetchall()
    return [dict(row) for row in rows]


def get_config(device_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM publisher_config WHERE device_id = ?", (device_id,)
        ).fetchone()
    if row is None:
        return {"device_id": device_id, **DEFAULT_CONFIG}
    cfg = dict(row)
    cfg["pausado"] = bool(cfg["pausado"])
    return cfg


def save_config(device_id: str, config: dict):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO publisher_config
                (device_id, intervalo, pausado, temp_min, temp_max,
                 humidity_min, humidity_max, falha_prob, falha_duracao_max)
            VALUES
                (:device_id, :intervalo, :pausado, :temp_min, :temp_max,
                 :humidity_min, :humidity_max, :falha_prob, :falha_duracao_max)
            ON CONFLICT(device_id) DO UPDATE SET
                intervalo         = excluded.intervalo,
                pausado           = excluded.pausado,
                temp_min          = excluded.temp_min,
                temp_max          = excluded.temp_max,
                humidity_min      = excluded.humidity_min,
                humidity_max      = excluded.humidity_max,
                falha_prob        = excluded.falha_prob,
                falha_duracao_max = excluded.falha_duracao_max
        """, {
            "device_id": device_id,
            **{k: DEFAULT_CONFIG[k] for k in DEFAULT_CONFIG},
            **config,
            "pausado": int(config.get("pausado", False)),
        })
