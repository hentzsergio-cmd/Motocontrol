import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from motocontrol.config import DATA_DIR, DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    ano INTEGER NOT NULL,
    placa TEXT NOT NULL UNIQUE,
    renavam TEXT DEFAULT '',
    data_compra TEXT DEFAULT '',
    valor_compra REAL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fuelings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    quilometragem REAL NOT NULL,
    litros REAL NOT NULL,
    valor REAL NOT NULL,
    posto TEXT DEFAULT '',
    tipo_combustivel TEXT DEFAULT '',
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS maintenances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    quilometragem REAL NOT NULL,
    categoria TEXT NOT NULL,
    descricao TEXT DEFAULT '',
    oficina TEXT DEFAULT '',
    valor REAL DEFAULT 0,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    descricao TEXT DEFAULT '',
    data_vencimento TEXT NOT NULL,
    valor REAL DEFAULT 0,
    observacao TEXT DEFAULT '',
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS financial_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER,
    data TEXT NOT NULL,
    categoria TEXT NOT NULL,
    descricao TEXT DEFAULT '',
    valor REAL NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS backup_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fuelings_vehicle ON fuelings(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_maintenances_vehicle ON maintenances(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_documents_vehicle ON documents(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_financial_vehicle ON financial_entries(vehicle_id);
"""

_DEFAULT_SETTINGS = {
    "theme": "dark",
    "backup_daily": "1",
    "backup_weekly": "1",
    "backup_monthly": "1",
    "last_backup_daily": "",
    "last_backup_weekly": "",
    "last_backup_monthly": "",
}


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(_SCHEMA)
        for key, value in _DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
        _run_migrations(conn)


def _run_migrations(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT value FROM settings WHERE key = 'schema_version'"
    ).fetchone()
    version = int(row["value"]) if row else 1
    if version < 2:
        for stmt in (
            "ALTER TABLE vehicles ADD COLUMN capacidade_tanque REAL DEFAULT 0",
            "ALTER TABLE fuelings ADD COLUMN tanque_cheio INTEGER DEFAULT 1",
        ):
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError:
                pass
        conn.execute(
            """
            INSERT INTO settings (key, value) VALUES ('schema_version', '2')
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """
        )


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]
