"""Web arayüzü: sunucu tarafında Jinja2 ile üretilen HTML sayfaları.

Sayfalar veritabanına doğrudan `api/db.py` üzerinden erişir (kendi API'mize HTTP isteği atmaz).
Doğrulama yine motorun `parse_test` fonksiyonuyla yapılır; yani CLI, API ve web aynı kuralları
ve aynı Türkçe hata mesajlarını kullanır.

Formlar klasik HTML formudur: POST -> işlem -> 303 ile yönlendirme (Post/Redirect/Get).
Böylece sayfa yenilenince form tekrar gönderilmez. JavaScript sadece editördeki canlı
doğrulama için kullanılır (web/static/editor.js); o olmadan da her şey çalışır.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from api import db
from api.artifacts import add_artifact_urls
from api.db import get_conn
from engine.dsl import DslError, parse_test

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
router = APIRouter(include_in_schema=False)  # /docs'ta görünmesin, orası JSON API için

NEW_TEST_TEMPLATE = """name: Yeni test
baseUrl: http://127.0.0.1:8000/demo
steps:
  - goto: /
  - fill: { label: Kullanıcı adı, value: demo }
  - fill: { label: Şifre, value: demo123 }
  - click: { role: button, name: Giriş yap }
  - expectUrl: /urunler.html
  - expectVisible: { role: heading, name: Ürünler }
"""

# ---------------------------------------------------------------------------
# Şablonlarda kullanılan küçük biçimlendiriciler
# ---------------------------------------------------------------------------

STATUS_LABELS = {
    "queued": "Sırada",
    "running": "Koşuyor",
    "passed": "Geçti",
    "failed": "Kaldı",
    "error": "Hata",
    "skipped": "Atlandı",
}


def format_ms(ms: Optional[int]) -> str:
    if ms is None:
        return "—"
    return f"{ms} ms" if ms < 1000 else f"{ms / 1000:.1f} sn".replace(".", ",")


def format_time(iso: Optional[str]) -> str:
    if not iso:
        return "—"
    return datetime.fromisoformat(iso).strftime("%d.%m.%Y %H:%M:%S")


templates.env.filters["ms"] = format_ms
templates.env.filters["time"] = format_time
templates.env.globals["STATUS_LABELS"] = STATUS_LABELS


def render(request: Request, name: str, status_code: int = 200, **context) -> HTMLResponse:
    return templates.TemplateResponse(request, name, context, status_code=status_code)


def redirect(url: str) -> RedirectResponse:
    # 303 See Other: "işlem tamam, şimdi şu sayfayı GET ile aç"
    return RedirectResponse(url, status_code=303)


def test_or_404(conn, test_id: int):
    row = db.get_test(conn, test_id)
    if row is None:
        raise HTTPException(404, f"{test_id} numaralı test bulunamadı")
    return row


# ---------------------------------------------------------------------------
# Testler
# ---------------------------------------------------------------------------

@router.get("/")
def tests_page(request: Request, conn=Depends(get_conn)):
    tests = db.list_tests(conn)
    queued = conn.execute("SELECT COUNT(*) FROM runs WHERE status IN ('queued', 'running')").fetchone()[0]
    return render(request, "tests.html", tests=tests, active_runs=queued)


@router.get("/tests/new")
def new_test_page(request: Request):
    return render(request, "test_edit.html", test=None, yaml_text=NEW_TEST_TEMPLATE, errors=[], runs=[])


@router.post("/tests/new")
def create_test(request: Request, yaml: str = Form(...), conn=Depends(get_conn)):
    try:
        test = parse_test(yaml, source="editör")
    except DslError as e:
        # Hatalıysa kaydetmeden aynı sayfayı, kullanıcının yazdıklarıyla ve hatalarla geri göster.
        return render(request, "test_edit.html", 422, test=None, yaml_text=yaml, errors=e.errors, runs=[])
    test_id = db.create_test(conn, test.name, yaml)
    return redirect(f"/tests/{test_id}?saved=1")


@router.get("/tests/{test_id}")
def edit_test_page(request: Request, test_id: int, conn=Depends(get_conn)):
    test = test_or_404(conn, test_id)
    runs = db.list_runs(conn, test_id=test_id, limit=10)
    return render(request, "test_edit.html", test=test, yaml_text=test["yaml"], errors=[], runs=runs,
                  saved=request.query_params.get("saved") == "1")


@router.post("/tests/{test_id}")
def update_test(request: Request, test_id: int, yaml: str = Form(...),
                conn=Depends(get_conn)):
    test = test_or_404(conn, test_id)
    try:
        parsed = parse_test(yaml, source="editör")
    except DslError as e:
        runs = db.list_runs(conn, test_id=test_id, limit=10)
        return render(request, "test_edit.html", 422, test=test, yaml_text=yaml, errors=e.errors, runs=runs)
    db.update_test(conn, test_id, parsed.name, yaml)
    return redirect(f"/tests/{test_id}?saved=1")


@router.post("/tests/{test_id}/delete")
def delete_test(test_id: int, conn=Depends(get_conn)):
    test_or_404(conn, test_id)
    db.delete_test(conn, test_id)
    return redirect("/")


@router.post("/tests/{test_id}/run")
def run_test(test_id: int, conn=Depends(get_conn)):
    run_id = db.create_run(conn, test_or_404(conn, test_id))
    return redirect(f"/runs/{run_id}")


@router.post("/run-all")
def run_all(conn=Depends(get_conn)):
    for test in db.list_tests(conn):
        db.create_run(conn, test)
    return redirect("/runs")


# ---------------------------------------------------------------------------
# Koşular ve rapor
# ---------------------------------------------------------------------------

@router.get("/runs")
def runs_page(request: Request, test_id: Optional[int] = None, status: Optional[str] = None,
              conn=Depends(get_conn)):
    if status not in (None, "", *STATUS_LABELS):
        status = None
    runs = db.list_runs(conn, test_id=test_id, status=status or None, limit=100)
    has_active = any(r["status"] in ("queued", "running") for r in runs)
    return render(request, "runs.html", runs=runs, tests=db.list_tests(conn),
                  test_id=test_id, status=status or "", has_active=has_active)


@router.get("/runs/{run_id}")
def run_report_page(request: Request, run_id: int, conn=Depends(get_conn)):
    run = db.get_run(conn, run_id)
    if run is None:
        raise HTTPException(404, f"{run_id} numaralı koşu bulunamadı")
    result = add_artifact_urls(json.loads(run["result_json"])) if run["result_json"] else None
    return render(request, "run_detail.html", run=run, result=result)
