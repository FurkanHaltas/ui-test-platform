"""Worker entegrasyon testi: kuyruk -> worker -> gerçek Chromium -> veritabanı.

İnternete bağımlı olmasın diye testin kendi küçük HTML sayfasını yerel bir HTTP sunucusunda
yayınlıyoruz. Headless Chromium açtığı için birim testlerinden yavaştır (birkaç saniye).
"""

import json
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest

import worker.main as worker
from api import db

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"></head><body>
  <h1>Merhaba</h1>
  <label for="ad">Ad</label><input id="ad">
  <button onclick="document.getElementById('sonuc').textContent = 'Selam ' + document.getElementById('ad').value">Gönder</button>
  <p id="sonuc"></p>
</body></html>
"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):  # test çıktısını kirletmesin
        pass


@pytest.fixture
def site(tmp_path):
    """Yerel bir web sitesi başlatır, adresini döndürür."""
    root = tmp_path / "site"
    root.mkdir()
    (root / "index.html").write_text(PAGE, encoding="utf-8")
    server = HTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture
def artifacts(tmp_path, monkeypatch):
    out = tmp_path / "artifacts"
    monkeypatch.setattr(worker, "ARTIFACTS_DIR", out)
    return out


def queue(conn, yaml_text: str) -> int:
    test = db.get_test(conn, db.create_test(conn, "t", yaml_text))
    return db.create_run(conn, test)


def test_worker_runs_passing_test(conn, site, artifacts):
    run_id = queue(conn, f"""
name: Form
baseUrl: {site}
steps:
  - goto: /index.html
  - fill: {{ label: Ad, value: Furkan }}
  - click: {{ role: button, name: Gönder }}
  - expectText: {{ css: "#sonuc", value: Selam Furkan }}
  - screenshot: son
""")
    assert worker.process_next(conn) is True
    run = db.get_run(conn, run_id)
    assert run["status"] == "passed", run["error"]
    result = json.loads(run["result_json"])
    assert [s["status"] for s in result["steps"]] == ["passed"] * 5
    assert Path(result["steps"][4]["screenshot"]).exists()
    assert result["trace"] is None  # geçen testte trace saklanmaz
    assert worker.process_next(conn) is False  # kuyruk boş


def test_worker_records_failure_with_screenshot_and_trace(conn, site, artifacts):
    run_id = queue(conn, f"""
name: Kalan
baseUrl: {site}
stepTimeout: 1000
steps:
  - goto: /index.html
  - expectVisible: {{ text: Böyle bir yazı yok }}
  - click: {{ role: button, name: Gönder }}
""")
    worker.process_next(conn)
    run = db.get_run(conn, run_id)
    assert run["status"] == "failed"
    assert run["error"].startswith("2. adım (expectVisible)")
    result = json.loads(run["result_json"])
    assert [s["status"] for s in result["steps"]] == ["passed", "failed", "skipped"]
    assert Path(result["steps"][1]["screenshot"]).exists()
    assert Path(result["trace"]).exists()
    # Her koşu kendi klasöründe
    assert Path(result["trace"]).is_relative_to(artifacts / "runs" / str(run_id))


def test_worker_marks_error_when_browser_cannot_start(conn, artifacts, monkeypatch):
    run_id = queue(conn, "name: X\nbaseUrl: https://a.com\nsteps:\n  - goto: /\n")

    def broken(*args, **kwargs):
        raise RuntimeError("tarayıcı yok")

    monkeypatch.setattr(worker, "run_tests", broken)
    worker.process_next(conn)
    run = db.get_run(conn, run_id)
    assert run["status"] == "error"
    assert "tarayıcı yok" in run["error"]
