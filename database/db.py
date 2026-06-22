import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sensor_data.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT    NOT NULL,
                temperature REAL  NOT NULL,
                humidity    REAL  NOT NULL,
                timestamp   TEXT  NOT NULL
            )
        """)


def insert_reading(data: dict):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO readings (device_id, temperature, humidity, timestamp)"
            " VALUES (?, ?, ?, ?)",
            (data["device_id"], data["temperature"], data["humidity"], data["timestamp"]),
        )
        # mantém apenas as últimas 24 horas
        conn.execute("DELETE FROM readings WHERE timestamp < datetime('now', '-24 hours')")


def get_latest_readings(limit: int = 10) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT device_id, temperature, humidity, timestamp"
            " FROM readings ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
