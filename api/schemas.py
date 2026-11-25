"""API'nin istek ve yanıt modelleri (Pydantic). FastAPI bunlardan /docs sayfasını otomatik üretir."""

from typing import Any, Optional

from pydantic import BaseModel


class TestIn(BaseModel):
    """Test oluşturma/güncelleme isteği: sadece YAML metni. Ad YAML'daki `name` alanından alınır."""

    __test__ = False  # pytest bu sınıfı test sanmasın
    yaml: str


class TestOut(BaseModel):
    __test__ = False
    id: int
    name: str
    yaml: str
    created_at: str
    updated_at: str
    last_run_id: Optional[int] = None
    last_run_status: Optional[str] = None


class ValidationOut(BaseModel):
    valid: bool
    errors: list[str] = []
    step_count: int = 0


class RunOut(BaseModel):
    id: int
    test_id: int
    test_name: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class RunDetailOut(RunOut):
    """Tek koşu: adım sonuçları ve ekran görüntüsü/trace adresleri dahil."""

    yaml: str
    result: Optional[dict[str, Any]] = None
