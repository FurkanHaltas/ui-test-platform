"""Demo sitesi + örnek testlerin entegrasyon testi (gerçek Chromium).

Sunumda canlı gösterilecek senaryonun bozulmadığını garanti eder:
  - examples/demo/ testleri Sürüm 1.0'da geçer,
  - sipariş testi Sürüm 2.0'da sepet toplamı adımında kalır (bilerek konmuş hata).
Site, API sunucusu yerine testin kendi açtığı yerel HTTP sunucusundan yayınlanır.
"""

import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from engine.dsl import load_test, parse_test
from engine.runner import run_tests

EXAMPLES = Path("examples/demo")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    """demo_site/ klasörünü /demo ve /demo-v2 altında yayınlar (API'deki adreslerle aynı)."""
    root = tmp_path_factory.mktemp("site")
    shutil.copytree("demo_site", root / "demo")
    shutil.copytree("demo_site", root / "demo-v2")
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def load_for(site: str, name: str):
    """Örnek testi okur ve adresini testin yerel sunucusuna çevirir."""
    text = (EXAMPLES / name).read_text(encoding="utf-8").replace("http://127.0.0.1:8000", site)
    return parse_test(text, source=name)


def test_all_demo_examples_are_valid():
    for path in EXAMPLES.glob("*.yaml"):
        load_test(path)


def test_v1_examples_pass(site, tmp_path):
    tests = [load_for(site, n) for n in ("giris.yaml", "kilitli-hesap.yaml", "siparis.yaml")]
    results = run_tests(tests, artifacts_dir=tmp_path)
    for r in results:
        assert r.status == "passed", f"{r.test_name}: {r.error}"


def test_v2_order_total_bug_is_caught(site, tmp_path):
    [result] = run_tests([load_for(site, "siparis-v2.yaml")], artifacts_dir=tmp_path)
    assert result.status == "failed"
    failed = [s for s in result.steps if s.status == "failed"]
    assert len(failed) == 1
    assert failed[0].description == 'expectText testId="sepet-toplami" = "3.650 TL"'
    assert "1.250 TL" in failed[0].error  # 2.0 sürümü son ürünü (klavye) saymıyor
    assert Path(failed[0].screenshot).exists()
