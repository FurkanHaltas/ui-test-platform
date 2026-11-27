"""Veritabanı katmanı ve iş kuyruğu mantığının birim testleri."""

from api import db

YAML = "name: A\nbaseUrl: https://a.com\nsteps:\n  - goto: /\n"


def make_test(conn, name="A"):
    return db.get_test(conn, db.create_test(conn, name, YAML))


def test_create_and_list_tests(conn):
    make_test(conn, "A")
    make_test(conn, "B")
    assert [t["name"] for t in db.list_tests(conn)] == ["A", "B"]


def test_queue_is_first_in_first_out(conn):
    t = make_test(conn)
    first = db.create_run(conn, t)
    second = db.create_run(conn, t)
    assert db.claim_next_run(conn)["id"] == first
    assert db.claim_next_run(conn)["id"] == second
    assert db.claim_next_run(conn) is None  # kuyruk boş


def test_claimed_run_is_running_and_not_claimed_twice(conn):
    run_id = db.create_run(conn, make_test(conn))
    claimed = db.claim_next_run(conn)
    assert claimed["status"] == "running"
    assert claimed["started_at"] is not None
    assert db.get_run(conn, run_id)["status"] == "running"
    assert db.claim_next_run(conn) is None


def test_run_keeps_yaml_snapshot(conn):
    t = make_test(conn)
    run_id = db.create_run(conn, t)
    db.update_test(conn, t["id"], "A", YAML.replace("goto: /", "goto: /yeni"))
    assert "goto: /yeni" not in db.get_run(conn, run_id)["yaml"]


def test_finish_run(conn):
    run_id = db.create_run(conn, make_test(conn))
    db.claim_next_run(conn)
    db.finish_run(conn, run_id, "failed", 1234, "3. adım kaldı", '{"steps": []}')
    run = db.get_run(conn, run_id)
    assert run["status"] == "failed"
    assert run["duration_ms"] == 1234
    assert run["finished_at"] is not None


def test_last_run_status_on_test(conn):
    t = make_test(conn)
    assert db.get_test(conn, t["id"])["last_run_status"] is None
    run_id = db.create_run(conn, t)
    row = db.get_test(conn, t["id"])
    assert row["last_run_id"] == run_id and row["last_run_status"] == "queued"


def test_stale_running_runs_become_error(conn):
    db.create_run(conn, make_test(conn))
    db.claim_next_run(conn)
    assert db.fail_stale_runs(conn) == 1
    assert db.list_runs(conn)[0]["status"] == "error"


def test_deleting_test_deletes_its_runs(conn):
    t = make_test(conn)
    db.create_run(conn, t)
    assert db.delete_test(conn, t["id"])
    assert db.list_runs(conn) == []


def test_list_runs_filters(conn):
    a, b = make_test(conn, "A"), make_test(conn, "B")
    db.create_run(conn, a)
    db.create_run(conn, b)
    db.claim_next_run(conn)  # A'nın koşusu running olur
    assert len(db.list_runs(conn, test_id=b["id"])) == 1
    assert [r["test_name"] for r in db.list_runs(conn, status="queued")] == ["B"]


def test_migration_adds_flaky_column_to_old_database(tmp_path, monkeypatch):
    """B2 öncesi oluşturulmuş bir veritabanı: runs tablosunda flaky sütunu yok."""
    import sqlite3

    path = tmp_path / "eski.db"
    old = sqlite3.connect(path)
    old.executescript("""
        CREATE TABLE tests (id INTEGER PRIMARY KEY, name TEXT, yaml TEXT, created_at TEXT, updated_at TEXT);
        CREATE TABLE runs (id INTEGER PRIMARY KEY, test_id INTEGER, test_name TEXT, yaml TEXT,
                           status TEXT, created_at TEXT, started_at TEXT, finished_at TEXT,
                           duration_ms INTEGER, error TEXT, result_json TEXT);
        INSERT INTO tests VALUES (1, 'A', 'y', 't', 't');
        INSERT INTO runs (test_id, test_name, yaml, status, created_at) VALUES (1, 'A', 'y', 'passed', 't');
    """)
    old.commit()
    old.close()

    monkeypatch.setenv("UITP_DB", str(path))
    conn = db.connect()
    db.init_db(conn)
    run = db.list_runs(conn)[0]
    assert run["flaky"] == 0  # sütun eklendi, eski kayıt korundu
    assert run["status"] == "passed"
    db.init_db(conn)  # ikinci kez çalıştırmak zararsız
    conn.close()


def test_finish_run_stores_flaky(conn):
    run_id = db.create_run(conn, make_test(conn))
    db.claim_next_run(conn)
    db.finish_run(conn, run_id, "passed", 10, None, "{}", flaky=True)
    assert db.get_run(conn, run_id)["flaky"] == 1
