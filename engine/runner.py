"""Test koşucu: TestDefinition'ı gerçek bir Chromium tarayıcıda adım adım uygular.

Akış (tek test için):
  1. Bu koşu için artifacts/<run_id>/ klasörü açılır.
  2. Yeni bir browser context açılır (temiz çerez/oturum = testler birbirini etkilemez).
  3. Trace (iz) kaydı başlatılır.
  4. Adımlar sırayla çalışır. Bir adım kalırsa: ekran görüntüsü alınır, kalan adımlar
     "skipped" olur, trace.zip kaydedilir.
  5. Sonuç result.json olarak yazılır ve RunResult döndürülür.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.sync_api import Browser, sync_playwright

from engine.dsl import TestDefinition
from engine.results import RunResult, StepResult
from engine.steps import Step, build_steps

DEFAULT_ARTIFACTS_DIR = Path("artifacts")


def run_tests(
    tests: list[TestDefinition],
    headed: bool = False,
    artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR,
    channel: Optional[str] = None,
) -> list[RunResult]:
    """Testleri sırayla koşturur. Tarayıcı bir kez açılır, her test kendi context'ini alır.

    channel=None -> Playwright'ın indirdiği Chromium; "chrome"/"msedge" -> bilgisayarda kurulu
    Chrome/Edge (ikisi de Chromium tabanlı, yani aynı motor).
    """
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed, channel=channel)
        try:
            for test in tests:
                # testId locator'ının hangi HTML özniteliğine bakacağı (ör. saucedemo: data-test)
                playwright.selectors.set_test_id_attribute(test.test_id_attribute)
                results.append(run_test(browser, test, artifacts_dir))
        finally:
            browser.close()
    return results


def run_test(browser: Browser, test: TestDefinition, artifacts_dir: Path) -> RunResult:
    """Tek bir testi koşturur ve sonucunu artifacts/<run_id>/result.json'a yazar."""
    started_at = datetime.now()
    run_id = f"{started_at:%Y%m%d-%H%M%S}_{slugify(test.name)}"
    run_dir = artifacts_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    steps = build_steps(test, run_dir)
    step_results: list[StepResult] = []
    run_error: Optional[str] = None
    trace_path: Optional[str] = None

    # Test bazında zaman aşımı: her adım en fazla kalan süre kadar bekleyebilir.
    start = time.monotonic()
    deadline = start + test.timeout / 1000

    context = browser.new_context(viewport={"width": 1280, "height": 720})
    context.tracing.start(screenshots=True, snapshots=True)
    page = context.new_page()
    try:
        for step in steps:
            if run_error is not None:
                # Önceki adım kaldı: bu adım çalıştırılmaz.
                step_results.append(_skipped(step))
                continue

            result = _run_step(page, step, test, deadline, run_dir)
            step_results.append(result)
            if result.status == "failed":
                run_error = f"{step.number}. adım ({step.kind}): {result.error}"
    finally:
        if run_error is not None:
            # Trace'i sadece kalan testlerde saklıyoruz; geçen testler için disk harcamıyoruz.
            trace_file = run_dir / "trace.zip"
            context.tracing.stop(path=str(trace_file))
            trace_path = str(trace_file)
        else:
            context.tracing.stop()
        context.close()

    finished_at = datetime.now()
    run = RunResult(
        run_id=run_id,
        test_name=test.name,
        source=test.source,
        base_url=test.base_url,
        status="failed" if run_error else "passed",
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=int((time.monotonic() - start) * 1000),
        error=run_error,
        trace=trace_path,
        steps=step_results,
    )
    run.save_json(run_dir / "result.json")
    return run


def _run_step(page, step: Step, test: TestDefinition, deadline: float, run_dir: Path) -> StepResult:
    """Tek adımı çalıştırır; başarısızsa hatayı yakalar ve ekran görüntüsü alır."""
    step_start = time.monotonic()
    remaining_ms = int((deadline - step_start) * 1000)
    if remaining_ms <= 0:
        return StepResult(
            number=step.number,
            kind=step.kind,
            description=step.describe(),
            status="failed",
            error=f"testin toplam süresi ({test.timeout} ms) doldu, adım başlatılamadı",
        )

    # Adımın kendi süresi, yoksa testin varsayılanı; ama asla kalan test süresinden fazla değil.
    timeout = min(step.timeout or test.step_timeout, remaining_ms)

    error = None
    screenshot = None
    try:
        screenshot = step.execute(page, timeout)
    except Exception as e:  # Playwright TimeoutError, expect'in AssertionError'ı vb.
        error = short_error(e)
        screenshot = _failure_screenshot(page, run_dir, step.number)

    return StepResult(
        number=step.number,
        kind=step.kind,
        description=step.describe(),
        status="failed" if error else "passed",
        duration_ms=int((time.monotonic() - step_start) * 1000),
        error=error,
        screenshot=screenshot,
    )


def _failure_screenshot(page, run_dir: Path, number: int) -> Optional[str]:
    """Hata anının ekran görüntüsü. Sayfa çökmüşse sessizce vazgeçer."""
    path = run_dir / f"hata-adim-{number}.png"
    try:
        page.screenshot(path=str(path), timeout=5_000)
        return str(path)
    except Exception:
        return None


def _skipped(step: Step) -> StepResult:
    return StepResult(
        number=step.number, kind=step.kind, description=step.describe(), status="skipped"
    )


def short_error(e: Exception) -> str:
    """Playwright hata mesajları uzun 'Call log' içerir; raporda sadece özet kısmı tutulur."""
    text = str(e).split("Call log:")[0]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    message = " | ".join(lines) or type(e).__name__
    if "Timeout" in message and "exceeded" in message:
        message = "zaman aşımı: öğe/koşul beklenen sürede bulunamadı — " + message
    return message


_TR_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def slugify(name: str) -> str:
    """'Başarılı giriş' -> 'basarili-giris' (klasör adı olarak güvenli)."""
    ascii_name = name.translate(_TR_ASCII).lower()
    parts = "".join(c if c.isalnum() else " " for c in ascii_name).split()
    return "-".join(parts)[:50] or "test"
