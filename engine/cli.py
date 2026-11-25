"""Komut satırı arayüzü.

Kullanım:
    python -m engine run examples/login.yaml          # tek test
    python -m engine run examples/                    # klasördeki tüm .yaml testleri
    python -m engine run examples/login.yaml --headed # tarayıcı görünür açılır
    python -m engine run examples/ --channel chrome   # kurulu Google Chrome ile
    python -m engine run x.yaml --update-baselines    # görsel referansları yeniden oluştur
    python -m engine validate examples/               # sadece YAML doğrulama, tarayıcı açmaz

Çıkış kodları: 0 = hepsi geçti, 1 = en az bir test kaldı, 2 = geçersiz YAML.
(CI'da, ör. GitHub Actions'ta, çıkış kodu 0 değilse iş kırmızı görünür.)
"""

import argparse
import sys
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError

from engine.console import use_utf8_output
from engine.dsl import DslError, TestDefinition, load_test
from engine.results import RunResult
from engine.runner import DEFAULT_ARTIFACTS_DIR, run_tests

# Renkler sadece gerçek terminalde; dosyaya yönlendirmede düz metin.
_COLOR = sys.stdout.isatty()
GREEN = "\033[32m" if _COLOR else ""
RED = "\033[31m" if _COLOR else ""
GRAY = "\033[90m" if _COLOR else ""
RESET = "\033[0m" if _COLOR else ""

ICONS = {"passed": f"{GREEN}✓{RESET}", "failed": f"{RED}✗{RESET}", "skipped": f"{GRAY}-{RESET}"}


def main(argv=None) -> int:
    use_utf8_output()

    parser = argparse.ArgumentParser(prog="python -m engine", description="YAML tabanlı UI test motoru")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="testleri tarayıcıda koştur")
    run_p.add_argument("paths", nargs="+", help=".yaml dosyaları veya klasörler")
    run_p.add_argument("--headed", action="store_true", help="tarayıcıyı görünür aç")
    run_p.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS_DIR,
                       help="çıktı klasörü (varsayılan: artifacts)")
    run_p.add_argument("--update-baselines", action="store_true",
                       help="expectScreenshot adımlarında karşılaştırma yapma, referansı güncelle")
    run_p.add_argument("--channel", choices=["chrome", "msedge"],
                       help="Playwright'ın Chromium'u yerine kurulu Chrome/Edge'i kullan")

    val_p = sub.add_parser("validate", help="YAML dosyalarını sadece doğrula")
    val_p.add_argument("paths", nargs="+", help=".yaml dosyaları veya klasörler")

    args = parser.parse_args(argv)

    tests = load_all(collect_files(args.paths))
    if tests is None:
        return 2
    if args.command == "validate":
        print(f"{GREEN}✓{RESET} {len(tests)} test dosyası geçerli.")
        return 0

    try:
        results = run_tests(tests, headed=args.headed, artifacts_dir=args.artifacts, channel=args.channel,
                            update_baselines=args.update_baselines)
    except PlaywrightError as e:
        # Genelde tarayıcı kurulmamıştır ya da başlatılamamıştır.
        print(f"{RED}✗ Tarayıcı başlatılamadı:{RESET} {str(e).splitlines()[0]}")
        print("  Kurulu değilse: python -m playwright install chromium")
        print("  Ya da bilgisayardaki Chrome ile deneyin: --channel chrome")
        return 2
    for run in results:
        print_run(run)
    print_summary(results)
    return 0 if all(r.status == "passed" for r in results) else 1


def collect_files(paths: list[str]) -> list[Path]:
    """Verilen yolları dosya listesine çevirir; klasörlerin içindeki .yaml/.yml dosyalarını alır."""
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted([*p.glob("*.yaml"), *p.glob("*.yml")]))
        else:
            files.append(p)
    return files


def load_all(files: list[Path]):
    """Tüm dosyaları doğrular. Biri bile geçersizse hataları basar ve None döndürür."""
    if not files:
        print(f"{RED}✗{RESET} Koşturulacak .yaml dosyası bulunamadı.")
        return None

    tests: list[TestDefinition] = []
    failed = False
    for f in files:
        try:
            tests.append(load_test(f))
        except DslError as e:
            failed = True
            print(f"{RED}✗ {e.source} geçersiz:{RESET}")
            for msg in e.errors:
                print(f"    - {msg}")
    if failed:
        print("\nTest koşturulmadı. Önce YAML hatalarını düzeltin.")
        return None
    return tests


def print_run(run: RunResult) -> None:
    print()
    print(f"{ICONS[run.status]} {run.test_name}  {GRAY}({format_ms(run.duration_ms)}, {run.source}){RESET}")
    for s in run.steps:
        timing = f"{GRAY}{format_ms(s.duration_ms):>7}{RESET}" if s.status != "skipped" else " " * 7
        print(f"    {ICONS[s.status]} {s.number:>2}. {timing}  {s.description}")
        if s.note:
            print(f"         {GRAY}{s.note}{RESET}")
        if s.error:
            print(f"         {RED}{s.error}{RESET}")
        if s.status == "failed" and s.screenshot:
            print(f"         {GRAY}ekran görüntüsü: {s.screenshot}{RESET}")
    if run.trace:
        print(f"    {GRAY}trace: {run.trace}  (açmak için: playwright show-trace {run.trace}){RESET}")


def print_summary(results: list[RunResult]) -> None:
    passed = sum(r.status == "passed" for r in results)
    failed = len(results) - passed
    total_ms = sum(r.duration_ms for r in results)
    color = GREEN if failed == 0 else RED
    print()
    print(f"{color}{passed} geçti, {failed} kaldı{RESET}  —  toplam {format_ms(total_ms)}")
    print(f"{GRAY}Ayrıntılı sonuçlar: artifacts/<run_id>/result.json{RESET}")


def format_ms(ms: int) -> str:
    return f"{ms} ms" if ms < 1000 else f"{ms / 1000:.1f} sn"
