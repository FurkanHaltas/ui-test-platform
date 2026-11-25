"""Örnek testleri (examples/demo/*.yaml ve examples/*.yaml) veritabanına yükler. Demo için.

    python -m api.seed

Aynı adda test zaten varsa atlar, yani birden fazla çalıştırmak güvenlidir.
"""

from pathlib import Path

from api import db
from engine.console import use_utf8_output
from engine.dsl import DslError, load_test


def main() -> None:
    use_utf8_output()
    conn = db.connect()
    db.init_db(conn)
    existing = {row["name"] for row in db.list_tests(conn)}
    # Önce internetsiz demo sitesinin testleri, sonra saucedemo.com testleri.
    paths = sorted(Path("examples/demo").glob("*.yaml")) + sorted(Path("examples").glob("*.yaml"))
    for path in paths:
        try:
            test = load_test(path)
        except DslError as e:
            print(f"✗ {path} atlandı: {e.errors[0]}")
            continue
        if test.name in existing:
            print(f"- {test.name} zaten var")
            continue
        test_id = db.create_test(conn, test.name, path.read_text(encoding="utf-8"))
        print(f"✓ #{test_id} {test.name}")
    conn.close()


if __name__ == "__main__":
    main()
