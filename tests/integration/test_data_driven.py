"""Veri odaklı testler (B3) — gerçek Chromium, yerel demo sitesi."""

import json
from pathlib import Path

from engine.dsl import parse_test
from engine.runner import run_tests
from tests.integration.test_demo_site import site  # noqa: F401  (yerel demo sunucusu)


def demo_test(site_url: str, name: str, version: str = "demo"):
    text = Path("examples/demo", name).read_text(encoding="utf-8")
    text = text.replace("http://127.0.0.1:8000/demo\n", f"{site_url}/{version}\n")
    return parse_test(text, source=f"{name} ({version})")


def test_invalid_login_rows_all_pass(site, tmp_path):  # noqa: F811
    [result] = run_tests([demo_test(site, "hatali-giris-veri.yaml")], artifacts_dir=tmp_path)

    assert result.status == "passed", result.error
    assert len(result.rows) == 4
    assert [r.status for r in result.rows] == ["passed"] * 4
    assert result.rows[2].data_row == {"kullanici": "", "sifre": "demo123", "mesaj": "Kullanıcı adı zorunlu."}
    assert result.rows[0].test_name.endswith("[1. satır]")
    # Yer tutucular doldurulmuş olarak raporlanır
    assert result.rows[1].steps[4].description == 'expectText testId="hata-mesaji" = "Kullanıcı adı veya şifre hatalı."'
    assert result.steps == []  # adımlar satırların içinde
    assert result.duration_ms == sum(r.duration_ms for r in result.rows)


def test_v2_bug_shows_up_only_for_rows_with_different_products(site, tmp_path):  # noqa: F811
    [result] = run_tests([demo_test(site, "sepet-toplami-veri.yaml", "demo-v2")], artifacts_dir=tmp_path)

    assert result.status == "failed"
    assert [r.status for r in result.rows] == ["failed", "failed", "passed"]
    assert result.error.startswith("2/3 satır kaldı; ilki Demo - Sepet toplamı (veri odaklı) [1. satır]")
    assert "1.250 TL" in result.rows[0].error  # 2.0 son ürünü (klavye) saymadı
    assert "850 TL" in result.rows[1].error  # 2.0 son ürünü (kablo) saymadı

    # Her satırın kendi klasörü ve kanıtları var; ana sonuç da diske yazıldı
    assert Path(result.rows[0].trace).exists()
    saved = json.loads((tmp_path / result.run_id / "result.json").read_text(encoding="utf-8"))
    assert len(saved["rows"]) == 3


def test_v1_all_cart_rows_pass(site, tmp_path):  # noqa: F811
    [result] = run_tests([demo_test(site, "sepet-toplami-veri.yaml")], artifacts_dir=tmp_path)
    assert result.status == "passed", result.error
    assert [r.data_row["toplam"] for r in result.rows] == ["3.650 TL", "1.000 TL", "2.500 TL"]
