"""SQLite veritabanı katmanı. API ve worker aynı dosyayı kullanır.

ORM yerine Python'un yerleşik `sqlite3` modülü ve düz SQL kullanıyoruz: iki tablo için
yeterli, her sorgu açıkça görünüyor ve savunmada anlatması kolay.

İş kuyruğu ayrı bir sistem değildir: `runs` tablosunda durumu 'queued' olan satırlar
kuyruktur. Worker bu satırları sırayla alır (claim_next_run).
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

# Koşu durumları: queued -> running -> passed | failed | error
#   failed: test çalıştı ama bir adım kaldı (testin bulduğu bir hata)
#   error : test hiç çalıştırılamadı (ör. tarayıcı açılamadı; platformun hatası)
FINAL_STATUSES = ("passed", "failed", "error")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tests (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    yaml        TEXT NOT NULL,            -- kullanıcının yazdığı YAML, yorumlarıyla birlikte
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id      INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    test_name    TEXT NOT NULL,
    yaml         TEXT NOT NULL,           -- kuyruğa alındığı andaki YAML'ın kopyası
    status       TEXT NOT NULL DEFAULT 'queued'
                 CHECK (status IN ('queued', 'running', 'passed', 'failed', 'error')),
    created_at   TEXT NOT NULL,
    started_at   TEXT,
    finished_at  TEXT,
    duration_ms  INTEGER,
    error        TEXT,
    result_json  TEXT                     -- motorun RunResult çıktısı (adımlar dahil)
);

CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status, id);
CREATE INDEX IF NOT EXISTS idx_runs_test ON runs(test_id, id);
"""


def db_path() -> Path:
    """Veritabanı dosyası. Testlerde UITP_DB ortam değişkeniyle geçici bir dosya verilir."""
    return Path(os.environ.get("UITP_DB", "data/platform.db"))


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # timeout: başka bir süreç (API/worker) yazarken 10 sn'ye kadar bekle, hemen hata verme.
    conn = sqlite3.connect(path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # satırlara row["name"] diye erişebilmek için
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL: biri yazarken diğerleri okuyabilir. API ve worker aynı anda çalıştığı için önemli.
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# tests tablosu
# ---------------------------------------------------------------------------

def create_test(conn, name: str, yaml_text: str) -> int:
    t = now()
    with conn:  # `with conn` = işlem (transaction): ya hepsi yazılır ya hiçbiri
        cur = conn.execute(
            "INSERT INTO tests (name, yaml, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (name, yaml_text, t, t),
        )
    return cur.lastrowid


def update_test(conn, test_id: int, name: str, yaml_text: str) -> bool:
    with conn:
        cur = conn.execute(
            "UPDATE tests SET name = ?, yaml = ?, updated_at = ? WHERE id = ?",
            (name, yaml_text, now(), test_id),
        )
    return cur.rowcount == 1


def delete_test(conn, test_id: int) -> bool:
    with conn:
        cur = conn.execute("DELETE FROM tests WHERE id = ?", (test_id,))
    return cur.rowcount == 1


def get_test(conn, test_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(f"{_TEST_SELECT} WHERE t.id = ?", (test_id,)).fetchone()


def list_tests(conn) -> list[sqlite3.Row]:
    return conn.execute(f"{_TEST_SELECT} ORDER BY t.id").fetchall()


# Her testi son koşusunun durumuyla birlikte getirir (liste ekranı için).
_TEST_SELECT = """
SELECT t.*,
       (SELECT r.id FROM runs r WHERE r.test_id = t.id ORDER BY r.id DESC LIMIT 1) AS last_run_id,
       (SELECT r.status FROM runs r WHERE r.test_id = t.id ORDER BY r.id DESC LIMIT 1) AS last_run_status
FROM tests t
"""


# ---------------------------------------------------------------------------
# runs tablosu (= iş kuyruğu)
# ---------------------------------------------------------------------------

def create_run(conn, test: sqlite3.Row) -> int:
    """Testi kuyruğa ekler. YAML kopyalanır: test sonradan düzenlense bile bu koşu değişmez."""
    with conn:
        cur = conn.execute(
            "INSERT INTO runs (test_id, test_name, yaml, created_at) VALUES (?, ?, ?, ?)",
            (test["id"], test["name"], test["yaml"], now()),
        )
    return cur.lastrowid


def get_run(conn, run_id: int) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()


def list_runs(conn, test_id: Optional[int] = None, status: Optional[str] = None,
              limit: int = 50) -> list[sqlite3.Row]:
    sql = "SELECT * FROM runs WHERE 1 = 1"
    params: list = []
    if test_id is not None:
        sql += " AND test_id = ?"
        params.append(test_id)
    if status is not None:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    return conn.execute(sql, params).fetchall()


def claim_next_run(conn) -> Optional[sqlite3.Row]:
    """Kuyruktaki en eski işi alır ve 'running' yapar. Tek bir SQL cümlesi olduğu için atomiktir:
    iki worker aynı anda çalışsa bile aynı işi ikisi birden alamaz."""
    with conn:
        return conn.execute(
            """
            UPDATE runs SET status = 'running', started_at = ?
            WHERE id = (SELECT id FROM runs WHERE status = 'queued' ORDER BY id LIMIT 1)
              AND status = 'queued'
            RETURNING *
            """,
            (now(),),
        ).fetchone()


def finish_run(conn, run_id: int, status: str, duration_ms: Optional[int],
               error: Optional[str], result_json: Optional[str]) -> None:
    assert status in FINAL_STATUSES
    with conn:
        conn.execute(
            """
            UPDATE runs SET status = ?, finished_at = ?, duration_ms = ?, error = ?, result_json = ?
            WHERE id = ?
            """,
            (status, now(), duration_ms, error, result_json, run_id),
        )


def fail_stale_runs(conn) -> int:
    """Worker başlarken 'running' kalmış koşuları 'error' yapar. Bunlar worker'ın
    önceki çalışmasında yarıda kalmış işlerdir (ör. pencere kapatıldı). MVP'de tek worker var."""
    with conn:
        cur = conn.execute(
            "UPDATE runs SET status = 'error', finished_at = ?, "
            "error = 'worker koşu sırasında durdu, koşu yarıda kaldı' WHERE status = 'running'",
            (now(),),
        )
    return cur.rowcount
