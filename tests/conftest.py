"""Testlerin ortak hazırlıkları (pytest fixture'ları)."""

from pathlib import Path

import pytest

from api import db


def pytest_collection_modifyitems(items):
    """E2E testlerini her zaman en sona al.

    pytest-playwright, ilk E2E testinden sonra oturum boyunca kendi Playwright örneğini açık tutar.
    Bundan sonra motoru aynı süreçte çağıran entegrasyon testleri "Sync API inside the asyncio
    loop" hatası alır. Sıralamayı burada garanti ediyoruz (bkz. hata kaydı H-11).
    """
    e2e_dir = Path(__file__).parent / "e2e"
    items.sort(key=lambda item: Path(item.fspath).is_relative_to(e2e_dir))


@pytest.fixture
def conn(tmp_path, monkeypatch):
    """Her test için boş, geçici bir SQLite veritabanı. Gerçek data/platform.db'ye dokunulmaz."""
    monkeypatch.setenv("UITP_DB", str(tmp_path / "test.db"))
    connection = db.connect()
    db.init_db(connection)
    yield connection
    connection.close()
