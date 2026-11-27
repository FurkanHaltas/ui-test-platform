"""Tekrar deneme ve kararsız test işareti (B2) — gerçek Chromium.

Rastgelelik yerine kontrollü bir sunucu kullanıyoruz: sayfa başlığı ancak N. istekten itibaren
görünür. Böylece "1. denemede kalıp 2. denemede geçen" test her seferinde aynı şekilde oluşur.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

import worker.main as worker
from api import db
from engine.dsl import parse_test
from engine.runner import run_tests


class Site:
    """`/sayfa` isteği `ready_after`. istekten itibaren başlığı gösterir; öncesinde boş sayfa."""

    def __init__(self, ready_after: int):
        self.ready_after = ready_after
        self.requests = 0


@pytest.fixture
def make_site():
    servers = []

    def start(ready_after: int) -> tuple[str, Site]:
        site = Site(ready_after)

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != "/sayfa":
                    self.send_error(404)
                    return
                site.requests += 1
                ready = site.requests >= site.ready_after
                body = "<h1>Hazır</h1>" if ready else "<p>Henüz değil</p>"
                data = f'<!doctype html><meta charset="utf-8">{body}'.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return f"http://127.0.0.1:{server.server_port}", site

    yield start
    for s in servers:
        s.shutdown()


def yaml_for(base: str, retries: int) -> str:
    return f"""
name: Tekrar deneme
baseUrl: {base}
retries: {retries}
steps:
  - goto: /sayfa
  - expectVisible: {{ role: heading, name: Hazır, timeout: 500 }}
"""


def test_flaky_test_passes_on_second_attempt_and_is_marked(make_site, tmp_path):
    base, site = make_site(ready_after=2)
    [result] = run_tests([parse_test(yaml_for(base, retries=2))], artifacts_dir=tmp_path)

    assert result.status == "passed"
    assert result.flaky is True
    assert result.attempt == 2
    assert site.requests == 2  # geçince durdu, 3. deneme yapılmadı

    [first] = result.previous_attempts
    assert first.attempt == 1 and first.status == "failed"
    assert first.error.startswith("2. adım (expectVisible)")
    assert Path(first.trace).exists()  # kalan denemenin kanıtları saklanır
    assert Path(first.steps[1].screenshot).exists()
    assert first.run_id != result.run_id  # her deneme kendi klasöründe

    # Toplam süre bütün denemeleri kapsar; ana result.json da güncel
    assert result.duration_ms > first.duration_ms >= 500  # 1. deneme en az timeout kadar bekledi
    saved = json.loads((tmp_path / result.run_id / "result.json").read_text(encoding="utf-8"))
    assert saved["flaky"] is True and len(saved["previous_attempts"]) == 1


def test_always_failing_test_uses_all_attempts(make_site, tmp_path):
    base, site = make_site(ready_after=99)
    [result] = run_tests([parse_test(yaml_for(base, retries=2))], artifacts_dir=tmp_path)

    assert result.status == "failed"
    assert result.flaky is False
    assert result.attempt == 3
    assert [a.attempt for a in result.previous_attempts] == [1, 2]
    assert site.requests == 3


def test_passing_test_is_not_retried(make_site, tmp_path):
    base, site = make_site(ready_after=1)
    [result] = run_tests([parse_test(yaml_for(base, retries=3))], artifacts_dir=tmp_path)
    assert result.status == "passed" and not result.flaky
    assert result.attempt == 1 and result.previous_attempts == []
    assert site.requests == 1


def test_without_retries_runs_once(make_site, tmp_path):
    base, site = make_site(ready_after=2)
    [result] = run_tests([parse_test(yaml_for(base, retries=0))], artifacts_dir=tmp_path)
    assert result.status == "failed" and result.previous_attempts == []
    assert site.requests == 1


def test_worker_stores_flaky_flag(make_site, conn, tmp_path, monkeypatch):
    monkeypatch.setattr(worker, "ARTIFACTS_DIR", tmp_path)
    base, _ = make_site(ready_after=2)
    test = db.get_test(conn, db.create_test(conn, "Tekrar deneme", yaml_for(base, retries=1)))
    run_id = db.create_run(conn, test)

    worker.process_next(conn)
    run = db.get_run(conn, run_id)
    assert run["status"] == "passed"
    assert run["flaky"] == 1
    assert db.get_test(conn, test["id"])["last_run_flaky"] == 1
