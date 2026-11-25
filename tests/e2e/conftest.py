"""E2E test altyapısı: platformun tamamını gerçek süreçler olarak ayağa kaldırır.

    uvicorn (API + web + demo sitesi)  ─┐
                                        ├─ geçici klasör: kendi veritabanı ve artifacts/'ı
    python -m worker                   ─┘

Testler pytest-playwright'ın `page` fixture'ıyla gerçek bir Chromium'da web arayüzünü kullanır.
Geliştiricinin data/platform.db dosyasına dokunulmaz.
"""

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]  # proje kökü


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_until_up(url: str, process: subprocess.Popen, timeout: float = 20) -> None:
    """Sunucu açılana kadar sağlık adresini yoklar. (Sunucu başlatma beklemesi; test adımı değil.)"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Sunucu başlamadan kapandı (çıkış kodu {process.returncode})")
        try:
            with urllib.request.urlopen(url, timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"Sunucu {timeout} sn içinde açılmadı: {url}")


@pytest.fixture(scope="session")
def platform(tmp_path_factory):
    """Sunucu ve worker'ı başlatır; testler bitince kapatır. Ana adresi döndürür."""
    workdir = tmp_path_factory.mktemp("platform")
    port = free_port()
    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT),
        "UITP_DB": str(workdir / "e2e.db"),
        "PYTHONUTF8": "1",
    }
    log = open(workdir / "server.log", "w", encoding="utf-8")
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--port", str(port)],
        cwd=workdir, env=env, stdout=log, stderr=subprocess.STDOUT,
    )
    worker = subprocess.Popen(
        [sys.executable, "-m", "worker", "--interval", "0.2"],
        cwd=workdir, env=env, stdout=log, stderr=subprocess.STDOUT,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        wait_until_up(base + "/api/health", server)
        yield base
    finally:
        for p in (worker, server):
            p.terminate()
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
        log.close()


@pytest.fixture(scope="session")
def base_url(platform):
    """pytest-playwright'ın `page.goto("/")` gibi göreli adresleri bu sunucuya yönlendirmesi için."""
    return platform


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    # Rapor ekran görüntüleriyle aynı boyut; Türkçe arayüz.
    return {**browser_context_args, "viewport": {"width": 1280, "height": 800}, "locale": "tr-TR"}
