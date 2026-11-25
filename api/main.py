"""FastAPI uygulaması: testleri kaydeder, koşuları kuyruğa alır, sonuçları sunar.

API testleri kendisi koşturmaz. "Koştur" isteği sadece runs tablosuna 'queued' bir satır
ekler ve hemen döner (202 Accepted). Asıl işi ayrı bir süreç olan worker yapar.
Böylece uzun süren tarayıcı işleri API'yi kilitlemez.

Aynı uygulama ayrıca şunları sunar:
  /            web arayüzü (web/routes.py, Jinja2 şablonları)
  /demo/       yerel demo sitesi Sürüm 1.0 (demo_site/)
  /demo-v2/    aynı site, Sürüm 2.0 (bilerek hatalı)
  /artifacts/  ekran görüntüleri ve trace dosyaları

Çalıştırma:  uvicorn api.main:app --reload
Arayüz:      http://127.0.0.1:8000
Belgeler:    http://127.0.0.1:8000/docs
"""

import json
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from api import db
from api.artifacts import add_artifact_urls
from api.db import get_conn
from api.schemas import RunDetailOut, RunOut, TestIn, TestOut, ValidationOut
from engine.dsl import DslError, TestDefinition, parse_test
from web.routes import router as web_router

ARTIFACTS_DIR = Path("artifacts")
ROOT_DIR = Path(__file__).resolve().parent.parent  # proje kökü


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama açılırken tabloları oluştur (zaten varsa dokunmaz).
    conn = db.connect()
    db.init_db(conn)
    conn.close()
    yield


app = FastAPI(
    title="Otomatik UI Test Platformu",
    description="YAML ile tanımlanan E2E testlerini kaydeder, kuyruğa alır ve sonuçlarını sunar.",
    version="0.3.0",
    lifespan=lifespan,
)

# Ekran görüntüleri ve trace dosyaları: /artifacts/runs/5/.../hata-adim-3.png
ARTIFACTS_DIR.mkdir(exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=ARTIFACTS_DIR), name="artifacts")
app.mount("/static", StaticFiles(directory=ROOT_DIR / "web" / "static"), name="static")
# Demo sitesi iki adreste: aynı dosyalar, sürümü JavaScript adres çubuğundan anlıyor.
app.mount("/demo", StaticFiles(directory=ROOT_DIR / "demo_site", html=True), name="demo")
app.mount("/demo-v2", StaticFiles(directory=ROOT_DIR / "demo_site", html=True), name="demo-v2")

# Web arayüzü sayfaları (/, /tests/..., /runs/...)
app.include_router(web_router)


def validate_or_422(yaml_text: str) -> TestDefinition:
    """YAML geçersizse 422 döner; gövdede motorun Türkçe hata listesi olur."""
    try:
        return parse_test(yaml_text, source="istek")
    except DslError as e:
        raise HTTPException(status_code=422, detail={"message": "Test tanımı geçersiz", "errors": e.errors})


def test_or_404(conn, test_id: int) -> sqlite3.Row:
    row = db.get_test(conn, test_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"{test_id} numaralı test bulunamadı")
    return row


# ---------------------------------------------------------------------------
# Genel
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["genel"])
def health(conn=Depends(get_conn)):
    queued = conn.execute("SELECT COUNT(*) FROM runs WHERE status = 'queued'").fetchone()[0]
    return {"status": "ok", "queued_runs": queued}


@app.post("/api/validate", response_model=ValidationOut, tags=["genel"])
def validate(body: TestIn):
    """YAML'ı kaydetmeden doğrular. Web arayüzündeki editör bunu canlı kontrol için kullanacak."""
    try:
        test = parse_test(body.yaml, source="istek")
        return ValidationOut(valid=True, step_count=len(test.steps))
    except DslError as e:
        return ValidationOut(valid=False, errors=e.errors)


# ---------------------------------------------------------------------------
# Testler
# ---------------------------------------------------------------------------

@app.get("/api/tests", response_model=list[TestOut], tags=["testler"])
def list_tests(conn=Depends(get_conn)):
    return [dict(r) for r in db.list_tests(conn)]


@app.post("/api/tests", response_model=TestOut, status_code=201, tags=["testler"])
def create_test(body: TestIn, conn=Depends(get_conn)):
    test = validate_or_422(body.yaml)
    test_id = db.create_test(conn, test.name, body.yaml)
    return dict(db.get_test(conn, test_id))


@app.get("/api/tests/{test_id}", response_model=TestOut, tags=["testler"])
def get_test(test_id: int, conn=Depends(get_conn)):
    return dict(test_or_404(conn, test_id))


@app.put("/api/tests/{test_id}", response_model=TestOut, tags=["testler"])
def update_test(test_id: int, body: TestIn, conn=Depends(get_conn)):
    test_or_404(conn, test_id)
    test = validate_or_422(body.yaml)
    db.update_test(conn, test_id, test.name, body.yaml)
    return dict(db.get_test(conn, test_id))


@app.delete("/api/tests/{test_id}", status_code=204, tags=["testler"])
def delete_test(test_id: int, conn=Depends(get_conn)):
    """Testi ve koşu kayıtlarını siler (ON DELETE CASCADE). Diskteki artifact dosyaları kalır."""
    if not db.delete_test(conn, test_id):
        raise HTTPException(status_code=404, detail=f"{test_id} numaralı test bulunamadı")


# ---------------------------------------------------------------------------
# Koşular
# ---------------------------------------------------------------------------

@app.post("/api/tests/{test_id}/runs", response_model=RunOut, status_code=202, tags=["koşular"])
def queue_run(test_id: int, conn=Depends(get_conn)):
    """Testi kuyruğa alır. 202 = 'isteği aldım, işlem daha sonra yapılacak'.
    Sonucu öğrenmek için GET /api/runs/{id} ile durum sorgulanır."""
    test = test_or_404(conn, test_id)
    run_id = db.create_run(conn, test)
    return dict(db.get_run(conn, run_id))


@app.get("/api/runs", response_model=list[RunOut], tags=["koşular"])
def list_runs(
    test_id: Optional[int] = None,
    status: Optional[str] = Query(None, pattern="^(queued|running|passed|failed|error)$"),
    limit: int = Query(50, ge=1, le=500),
    conn=Depends(get_conn),
):
    return [dict(r) for r in db.list_runs(conn, test_id=test_id, status=status, limit=limit)]


@app.get("/api/runs/{run_id}", response_model=RunDetailOut, tags=["koşular"])
def get_run(run_id: int, conn=Depends(get_conn)):
    row = db.get_run(conn, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"{run_id} numaralı koşu bulunamadı")
    data = dict(row)
    result_json = data.pop("result_json")
    data["result"] = add_artifact_urls(json.loads(result_json)) if result_json else None
    return data
