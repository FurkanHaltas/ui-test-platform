"""JUnit XML'den GitHub Actions iş özeti (Markdown) üretir.

Kullanım: python .github/scripts/test_ozeti.py reports/junit.xml >> "$GITHUB_STEP_SUMMARY"
"""

import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # Windows konsolunda da ✅ ❌ basılabilsin
path = Path(sys.argv[1])
if not path.exists():
    print("## Test özeti\n\nTest raporu oluşmadı (testler başlayamadan iş durdu).")
    sys.exit(0)

suite = ET.parse(path).getroot()
suite = suite if suite.tag == "testsuite" else suite.find("testsuite")

groups = defaultdict(lambda: {"passed": 0, "failed": 0, "skipped": 0, "time": 0.0})
failures = []
for case in suite.iter("testcase"):
    # classname ör. "tests.unit.test_dsl" -> grup "unit"
    parts = case.get("classname", "").split(".")
    group = parts[1] if len(parts) > 1 else "diğer"
    g = groups[group]
    g["time"] += float(case.get("time", 0))
    if case.find("failure") is not None or case.find("error") is not None:
        g["failed"] += 1
        failures.append(f"{case.get('classname')}::{case.get('name')}")
    elif case.find("skipped") is not None:
        g["skipped"] += 1
    else:
        g["passed"] += 1

total_failed = sum(g["failed"] for g in groups.values())
total = sum(g["passed"] + g["failed"] + g["skipped"] for g in groups.values())
print(f"## Test özeti {'✅' if total_failed == 0 else '❌'}\n")
print(f"**{total - total_failed} / {total}** test geçti.\n")
print("| Katman | Geçti | Kaldı | Atlandı | Süre |")
print("|--------|------:|------:|--------:|-----:|")
names = {"unit": "Birim", "integration": "Entegrasyon", "e2e": "E2E"}
for key in ("unit", "integration", "e2e", *sorted(set(groups) - {"unit", "integration", "e2e"})):
    if key in groups:
        g = groups[key]
        print(f"| {names.get(key, key)} | {g['passed']} | {g['failed']} | {g['skipped']} | {g['time']:.1f} sn |")
if failures:
    print("\n### Kalan testler\n")
    for f in failures:
        print(f"- `{f}`")
