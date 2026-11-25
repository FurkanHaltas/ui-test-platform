"""API uç noktalarının testleri. FastAPI'nin TestClient'ı sunucu açmadan istek gönderir."""

import json

import pytest
from fastapi.testclient import TestClient

from api import db
from api.main import app

VALID = """name: Giriş testi
baseUrl: https://www.saucedemo.com
steps:
  - goto: /
  - click: { role: button, name: Login }
"""


@pytest.fixture
def client(conn):  # conn fixture'ı UITP_DB'yi geçici dosyaya yönlendirir
    with TestClient(app) as c:
        yield c


def create(client, yaml_text=VALID):
    r = client.post("/api/tests", json={"yaml": yaml_text})
    assert r.status_code == 201, r.text
    return r.json()


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok", "queued_runs": 0}


def test_create_test_takes_name_from_yaml(client):
    t = create(client)
    assert t["name"] == "Giriş testi"
    assert t["yaml"] == VALID
    assert client.get(f"/api/tests/{t['id']}").json()["name"] == "Giriş testi"


def test_invalid_yaml_returns_422_with_turkish_errors(client):
    r = client.post("/api/tests", json={"yaml": VALID.replace("click", "tikla")})
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["message"] == "Test tanımı geçersiz"
    assert "bilinmeyen adım tipi 'tikla'" in detail["errors"][0]
    assert client.get("/api/tests").json() == []  # kaydedilmedi


def test_validate_endpoint(client):
    ok = client.post("/api/validate", json={"yaml": VALID}).json()
    assert ok == {"valid": True, "errors": [], "step_count": 2}
    bad = client.post("/api/validate", json={"yaml": "name: X\n"}).json()
    assert bad["valid"] is False
    assert any("baseUrl" in e for e in bad["errors"])


def test_update_and_delete_test(client):
    t = create(client)
    r = client.put(f"/api/tests/{t['id']}", json={"yaml": VALID.replace("Giriş testi", "Yeni ad")})
    assert r.status_code == 200 and r.json()["name"] == "Yeni ad"
    assert client.delete(f"/api/tests/{t['id']}").status_code == 204
    assert client.get(f"/api/tests/{t['id']}").status_code == 404


def test_missing_test_is_404_in_turkish(client):
    r = client.get("/api/tests/999")
    assert r.status_code == 404
    assert "bulunamadı" in r.json()["detail"]
    assert client.post("/api/tests/999/runs").status_code == 404


def test_queue_run_returns_202_and_queued(client):
    t = create(client)
    r = client.post(f"/api/tests/{t['id']}/runs")
    assert r.status_code == 202
    run = r.json()
    assert run["status"] == "queued" and run["test_id"] == t["id"]
    assert client.get("/api/health").json()["queued_runs"] == 1
    assert client.get(f"/api/tests/{t['id']}").json()["last_run_status"] == "queued"


def test_run_detail_has_result_and_artifact_urls(client, conn):
    t = create(client)
    run_id = client.post(f"/api/tests/{t['id']}/runs").json()["id"]
    # Worker'ın yapacağını elle taklit ediyoruz.
    db.claim_next_run(conn)
    result = {
        "status": "failed",
        "trace": "artifacts/runs/1/x/trace.zip",
        "steps": [
            {"number": 1, "status": "passed", "screenshot": None},
            {"number": 2, "status": "failed", "screenshot": "artifacts/runs/1/x/hata-adim-2.png"},
        ],
    }
    db.finish_run(conn, run_id, "failed", 500, "2. adım kaldı", json.dumps(result))

    detail = client.get(f"/api/runs/{run_id}").json()
    assert detail["status"] == "failed"
    assert detail["error"] == "2. adım kaldı"
    assert detail["result"]["trace_url"] == "/artifacts/runs/1/x/trace.zip"
    assert detail["result"]["steps"][0]["screenshot_url"] is None
    assert detail["result"]["steps"][1]["screenshot_url"] == "/artifacts/runs/1/x/hata-adim-2.png"


def test_list_runs_filters(client):
    a, b = create(client), create(client, VALID.replace("Giriş testi", "B"))
    client.post(f"/api/tests/{a['id']}/runs")
    client.post(f"/api/tests/{b['id']}/runs")
    assert len(client.get("/api/runs").json()) == 2
    assert [r["test_name"] for r in client.get(f"/api/runs?test_id={b['id']}").json()] == ["B"]
    assert client.get("/api/runs?status=passed").json() == []
    assert client.get("/api/runs?status=yanlis").status_code == 422
