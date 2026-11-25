"""Motorun yazdığı dosya yollarını tarayıcıda açılabilir adreslere çevirir.

Motor:   artifacts/runs/5/20261125-..._giris/hata-adim-3.png
Tarayıcı: /artifacts/runs/5/20261125-..._giris/hata-adim-3.png   (api/main.py'deki StaticFiles)
"""

from typing import Optional


def to_url(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    return "/" + path.replace("\\", "/").lstrip("/")


def add_artifact_urls(result: dict) -> dict:
    """Sonuç sözlüğüne her adım için `screenshot_url`, koşu için `trace_url` ekler."""
    for step in result.get("steps", []):
        step["screenshot_url"] = to_url(step.get("screenshot"))
    result["trace_url"] = to_url(result.get("trace"))
    return result
