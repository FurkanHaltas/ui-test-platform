"""Worker: kuyruktaki ('queued') koşuları sırayla alır ve test motoruyla çalıştırır.

API'den ayrı bir süreçtir. API "şunu koştur" der, worker koşturur, sonucu veritabanına yazar.

Çalıştırma:
    python -m worker                   # sürekli çalışır, Ctrl+C ile durur
    python -m worker --once            # kuyruktakileri bitirir ve çıkar (testler/CI için)
    python -m worker --channel chrome  # kurulu Chrome ile
"""

import argparse
import time
from pathlib import Path
from typing import Optional

from api import db
from engine.console import use_utf8_output
from engine.dsl import parse_test
from engine.runner import run_tests

ARTIFACTS_DIR = Path("artifacts")


def process_next(conn, channel: Optional[str] = None) -> bool:
    """Kuyruktan bir iş alır ve çalıştırır. Kuyruk boşsa False döner."""
    run = db.claim_next_run(conn)
    if run is None:
        return False

    print(f"→ #{run['id']} {run['test_name']} koşuluyor...", flush=True)
    try:
        # YAML kaydedilirken doğrulandı; yine de motor bu kopyayı tekrar okur.
        test = parse_test(run["yaml"], source=f"test#{run['test_id']}")
        # Her koşunun dosyaları kendi klasöründe: artifacts/runs/<koşu no>/...
        [result] = run_tests([test], artifacts_dir=ARTIFACTS_DIR / "runs" / str(run["id"]),
                             channel=channel)
        db.finish_run(conn, run["id"], result.status, result.duration_ms,
                      result.error, result.model_dump_json(), flaky=result.flaky)
        icon = "✓" if result.status == "passed" else "✗"
        flaky = f", kararsız: {result.attempt}. denemede geçti" if result.flaky else ""
        print(f"  {icon} #{run['id']} {result.status} ({result.duration_ms} ms{flaky})", flush=True)
    except Exception as e:
        # Test hiç çalıştırılamadı (tarayıcı açılamadı vb.): testin değil platformun hatası.
        message = f"koşu başlatılamadı: {str(e).splitlines()[0] if str(e) else type(e).__name__}"
        db.finish_run(conn, run["id"], "error", None, message, None)
        print(f"  ! #{run['id']} error: {message}", flush=True)
    return True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m worker", description="Test koşu kuyruğu işleyicisi")
    parser.add_argument("--once", action="store_true", help="kuyruk boşalınca çık")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="kuyruk boşken kaç saniyede bir bakılsın (varsayılan 1)")
    parser.add_argument("--channel", choices=["chrome", "msedge"], help="kurulu Chrome/Edge'i kullan")
    args = parser.parse_args(argv)
    use_utf8_output()

    conn = db.connect()
    db.init_db(conn)
    stale = db.fail_stale_runs(conn)
    if stale:
        print(f"! Yarıda kalmış {stale} koşu 'error' olarak işaretlendi.")
    print(f"Worker başladı (veritabanı: {db.db_path()}). Durdurmak için Ctrl+C.", flush=True)

    try:
        while True:
            worked = process_next(conn, channel=args.channel)
            if not worked:
                if args.once:
                    break
                # Kuyruk boş: veritabanını yormamak için kısa bir bekleme (polling).
                # Bu, test adımlarındaki "sabit sleep" yasağıyla ilgili değildir; testi etkilemez.
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nWorker durduruldu.")
    finally:
        conn.close()
    return 0
