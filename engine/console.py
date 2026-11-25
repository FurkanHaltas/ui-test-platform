"""Konsol çıktısı yardımcıları."""

import sys


def use_utf8_output() -> None:
    """Çıktı bir dosyaya/boruya giderken Windows eski kod sayfasını (cp1254) kullanır ve
    ✓ ✗ → gibi karakterlerde çöker. Bu durumda çıktıyı UTF-8'e çeviriyoruz."""
    if not sys.stdout.isatty():
        sys.stdout.reconfigure(encoding="utf-8")
