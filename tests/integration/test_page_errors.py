"""Otomatik sayfa hatası yakalama (B1) testleri — gerçek Chromium.

Demo sitesi: Sürüm 1.0 temiz olmalı (gürültü yok), Sürüm 2.0'daki üç bilinçli hata yakalanmalı.
Ayrıca küçük bir yerel sayfayla ağ hatası, tekrarlanan hata ve favicon gürültüsü sınanır.
"""

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from engine.dsl import parse_test
from engine.runner import run_tests
from tests.integration.test_demo_site import site  # noqa: F401  (yerel demo sunucusu)


def demo_test(site_url: str, name: str, version: str = "demo", extra_root: str = ""):
    """Demo örnek testini okur; adresi testin yerel sunucusuna ve istenen sürüme çevirir."""
    text = Path("examples/demo", name).read_text(encoding="utf-8")
    text = text.replace("http://127.0.0.1:8000/demo\n", f"{site_url}/{version}\n")
    if extra_root:
        text = text.replace("steps:", f"{extra_root}\nsteps:", 1)
    return parse_test(text, source=f"{name} ({version})")


def kinds(result) -> set[str]:
    return {e.kind for e in result.page_errors}


def test_v1_has_no_page_errors(site, tmp_path):  # noqa: F811
    # Gürültü filtresi doğru mu? Temiz sitede tek bir hata bile raporlanmamalı.
    [result] = run_tests([demo_test(site, "siparis.yaml")], artifacts_dir=tmp_path)
    assert result.status == "passed", result.error
    assert result.page_errors == []


def test_v2_page_errors_are_caught_without_any_test_step(site, tmp_path):  # noqa: F811
    # giris.yaml'da sayfa hatalarıyla ilgili hiçbir adım yok; yine de yakalanmalı.
    [result] = run_tests([demo_test(site, "giris.yaml", "demo-v2")], artifacts_dir=tmp_path)

    assert result.status == "passed"  # varsayılan: sadece uyarı, test kalmaz
    assert kinds(result) == {"console", "http", "exception"}
    by_kind = {e.kind: e for e in result.page_errors}
    assert by_kind["console"].message == "Kampanya servisine ulaşılamadı"
    assert by_kind["http"].message.startswith("HTTP 404")
    assert by_kind["http"].url.endswith("/img/kampanya-banner.png")
    assert by_kind["exception"].message.startswith("TypeError: ")
    assert "sayfaGoruntulendi" in by_kind["exception"].message
    # Her hata, oluştuğu sırada çalışan adıma yazılır
    assert all(e.step is not None for e in result.page_errors)


def test_fail_on_page_errors_makes_the_test_fail(site, tmp_path):  # noqa: F811
    v1 = demo_test(site, "giris.yaml", "demo", extra_root="failOnPageErrors: true")
    v2 = demo_test(site, "giris.yaml", "demo-v2", extra_root="failOnPageErrors: true")
    r1, r2 = run_tests([v1, v2], artifacts_dir=tmp_path)
    assert r1.status == "passed", r1.error
    assert r2.status == "failed"
    assert r2.error.startswith("sayfada 3 hata yakalandı")
    assert all(s.status == "passed" for s in r2.steps)  # adımlar geçti, sayfa hatalı
    assert r2.trace is not None  # kalan testte trace saklanır


# --- Yerel sayfa: ağ hatası, tekrarlanan hata, favicon gürültüsü ------------------

PAGE = """<!doctype html><html><head><meta charset="utf-8"></head><body>
<h1>Hata sayfası</h1>
<script src="http://127.0.0.1:9/yok.js"></script>
<script>for (let i = 0; i < 3; i++) console.error("tekrarlanan hata");</script>
</body></html>
"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture
def error_page(tmp_path):
    root = tmp_path / "site"
    root.mkdir()
    (root / "index.html").write_text(PAGE, encoding="utf-8")  # favicon.ico yok -> 404 olur
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_network_errors_duplicates_and_favicon(error_page, tmp_path):
    test = parse_test(f"""
name: Hatalı sayfa
baseUrl: {error_page}
steps:
  - goto: /index.html
  - expectVisible: {{ role: heading, name: Hata sayfası }}
""")
    [result] = run_tests([test], artifacts_dir=tmp_path)
    by_kind = {e.kind: e for e in result.page_errors}

    # Kapalı porta istek -> "network" (sunucuya hiç ulaşılamadı)
    assert by_kind["network"].url == "http://127.0.0.1:9/yok.js"
    # Aynı konsol hatası 3 kez -> tek kayıt, sayısı 3
    assert by_kind["console"].message == "tekrarlanan hata"
    assert by_kind["console"].count == 3
    # Tarayıcının kendiliğinden istediği favicon.ico'nun 404'ü hata sayılmaz
    assert not any(e.url and e.url.endswith("favicon.ico") for e in result.page_errors)
