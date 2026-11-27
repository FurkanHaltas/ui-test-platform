"""Koşu sonucu modeli: bir test koşusu -> adım sonuçları. JSON dosyasına yazılır.

Sonraki aşamada API ve web arayüzü de aynı modeli (ve aynı JSON'u) kullanacak.
"""

from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel

StepStatus = Literal["passed", "failed", "skipped"]
RunStatus = Literal["passed", "failed"]


class StepResult(BaseModel):
    number: int
    kind: str  # adım tipi, ör. "click"
    description: str  # ör. role=button[name="Login"]
    status: StepStatus
    duration_ms: int = 0
    error: Optional[str] = None  # sadece başarısız adımda dolu
    screenshot: Optional[str] = None  # screenshot adımı ya da hata anı görüntüsü
    # Sadece expectScreenshot adımında:
    note: Optional[str] = None  # ör. "Referansla fark: %0.000 (0 piksel)"
    baseline: Optional[str] = None  # karşılaştırılan referansın bu koşudaki kopyası
    diff: Optional[str] = None  # fark görüntüsü (değişen pikseller kırmızı)
    baseline_source: Optional[str] = None  # asıl referans dosyası ("Referansı güncelle" için)


class PageError(BaseModel):
    """Test koşarken sayfada kendiliğinden oluşan hata (bkz. engine/page_errors.py)."""

    kind: Literal["console", "exception", "http", "network"]
    message: str
    url: Optional[str] = None  # hatalı kaynağın ya da betiğin adresi
    step: Optional[int] = None  # hata olduğunda çalışan adım
    count: int = 1  # aynı hata kaç kez tekrarlandı


class RunResult(BaseModel):
    run_id: str  # ör. 20261125-142301_basarili-giris
    test_name: str
    source: str  # YAML dosyasının yolu
    base_url: str
    status: RunStatus
    started_at: datetime
    finished_at: datetime
    duration_ms: int
    error: Optional[str] = None  # testin neden kaldığı (ilk başarısız adımın hatası)
    trace: Optional[str] = None  # sadece kalan testlerde kaydedilir
    page_errors: list[PageError] = []  # test yazılmadan yakalanan sayfa hataları (B1)
    steps: list[StepResult]

    def save_json(self, path: Path) -> None:
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load_json(cls, path: Path) -> "RunResult":
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))
