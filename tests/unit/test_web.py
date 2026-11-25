"""Web arayüzü sayfalarının testleri (HTML çıktısı, formlar, yönlendirmeler)."""

import json

import pytest
from fastapi.testclient import TestClient

from api import db
from api.main import app

VALID = """name: Web testi
baseUrl: http://127.0.0.1:8000/demo
steps:
  - goto: /
  - click: { role: button, name: Giriş yap }
"""


@pytest.fixture
def client(conn):
    with TestClient(app) as c:
        yield c


def create(client, yaml_text=VALID) -> int:
    r = client.post("/tests/new", data={"yaml": yaml_text}, follow_redirects=False)
    assert r.status_code == 303, r.text
    return int(r.headers["location"].split("/")[2].split("?")[0])


def test_empty_test_list_shows_hint(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Henüz test yok" in r.text
    assert "python -m api.seed" in r.text


def test_new_test_page_has_editor_with_template(client):
    r = client.get("/tests/new")
    assert r.status_code == 200
    assert '<textarea id="yaml" name="yaml"' in r.text
    assert "baseUrl: http://127.0.0.1:8000/demo" in r.text


def test_create_test_redirects_and_appears_in_list(client):
    test_id = create(client)
    page = client.get(f"/tests/{test_id}?saved=1").text
    assert "Kaydedildi" in page
    assert "Web testi" in client.get("/").text


def test_invalid_test_shows_errors_and_keeps_text(client):
    bad = VALID.replace("click", "tikla")
    r = client.post("/tests/new", data={"yaml": bad})
    assert r.status_code == 422
    assert "Test tanımı geçersiz" in r.text
    assert "bilinmeyen adım tipi" in r.text
    assert "tikla" in r.text  # kullanıcının yazdığı kaybolmadı
    assert db.list_tests(db.connect()) == []


def test_user_text_is_escaped(client):
    # Kullanıcının YAML'ı sayfaya HTML olarak değil, düz metin olarak basılmalı (XSS koruması).
    r = client.post("/tests/new", data={"yaml": VALID + "  - foo: <script>alert(1)</script>\n"})
    assert "<script>alert(1)</script>" not in r.text
    assert "&lt;script&gt;" in r.text


def test_update_and_delete(client):
    test_id = create(client)
    r = client.post(f"/tests/{test_id}", data={"yaml": VALID.replace("Web testi", "Yeni ad")},
                    follow_redirects=False)
    assert r.status_code == 303
    assert "Yeni ad" in client.get(f"/tests/{test_id}").text
    r = client.post(f"/tests/{test_id}/delete", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/"
    assert client.get(f"/tests/{test_id}").status_code == 404


def test_run_button_queues_and_redirects_to_report(client):
    test_id = create(client)
    r = client.post(f"/tests/{test_id}/run", follow_redirects=False)
    assert r.status_code == 303
    report = client.get(r.headers["location"]).text
    assert "Sırada" in report
    assert 'http-equiv="refresh"' in report  # bitene kadar otomatik yenilenir
    assert "python -m worker" in report  # worker ipucu


def test_run_all_queues_every_test(client):
    create(client)
    create(client, VALID.replace("Web testi", "İkinci"))
    r = client.post("/run-all", follow_redirects=False)
    assert r.headers["location"] == "/runs"
    assert len(db.list_runs(db.connect(), status="queued")) == 2


def test_finished_report_shows_steps_screenshot_and_trace(client, conn):
    test_id = create(client)
    run_id = db.create_run(conn, db.get_test(conn, test_id))
    db.claim_next_run(conn)
    result = {
        "base_url": "http://127.0.0.1:8000/demo",
        "trace": "artifacts/runs/1/x/trace.zip",
        "steps": [
            {"number": 1, "description": "goto http://127.0.0.1:8000/demo/", "status": "passed",
             "duration_ms": 120, "error": None, "screenshot": None},
            {"number": 2, "description": 'click role=button[name="Giriş yap"]', "status": "failed",
             "duration_ms": 3000, "error": "zaman aşımı", "screenshot": "artifacts/runs/1/x/hata-adim-2.png"},
        ],
    }
    db.finish_run(conn, run_id, "failed", 3200, "2. adım (click): zaman aşımı", json.dumps(result))

    page = client.get(f"/runs/{run_id}").text
    assert "Kaldı" in page
    assert "Testin kaldığı yer" in page
    assert 'src="/artifacts/runs/1/x/hata-adim-2.png"' in page
    assert 'href="/artifacts/runs/1/x/trace.zip"' in page
    assert "3,2 sn" in page
    assert 'http-equiv="refresh"' not in page  # bitmiş koşu yenilenmez


def test_runs_page_filters(client, conn):
    a = create(client)
    b = create(client, VALID.replace("Web testi", "Diğer test"))
    db.create_run(conn, db.get_test(conn, a))
    db.create_run(conn, db.get_test(conn, b))
    page = client.get(f"/runs?test_id={b}").text
    # Tablo satırlarında sadece süzülen testin koşusu olmalı (açılır listede ise tüm testler var).
    assert 'class="strong">Diğer test</a>' in page
    assert 'class="strong">Web testi</a>' not in page
    assert client.get("/runs?status=yanlis").status_code == 200  # geçersiz süzgeç yok sayılır


def test_missing_pages_are_404(client):
    assert client.get("/tests/999").status_code == 404
    assert client.get("/runs/999").status_code == 404


def test_demo_site_is_served_in_two_versions(client):
    assert "Mini Market" in client.get("/demo/").text
    assert "Mini Market" in client.get("/demo-v2/").text
    assert client.get("/demo/app.js").status_code == 200
