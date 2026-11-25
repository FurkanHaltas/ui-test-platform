"""Testlerin ortak hazırlıkları (pytest fixture'ları)."""

import pytest

from api import db


@pytest.fixture
def conn(tmp_path, monkeypatch):
    """Her test için boş, geçici bir SQLite veritabanı. Gerçek data/platform.db'ye dokunulmaz."""
    monkeypatch.setenv("UITP_DB", str(tmp_path / "test.db"))
    connection = db.connect()
    db.init_db(connection)
    yield connection
    connection.close()
