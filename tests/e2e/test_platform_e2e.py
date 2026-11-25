"""Platformun kendi uçtan uca (E2E) testleri.

Gerçek sunucu + gerçek worker + gerçek Chromium. Kullanıcının yaptığını yapar: sayfaları açar,
yazar, tıklar ve ekranda gördüğünü doğrular. Her test, gereksinim analizindeki bir kullanıcı
hikâyesine karşılık gelir (rapor/02-gereksinim-analizi.md).

Not: Kendi testlerimizde de sabit bekleme yok. Koşunun bitmesini, rapor sayfası kendini
yeniledikçe `expect(...)` ile bekliyoruz.
"""

import json
import re
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

ROOT = Path(__file__).resolve().parents[2]
RUN_TIMEOUT = 30_000  # bir koşunun sırada bekleyip bitmesi için üst sınır (ms)


def example(name: str, base: str) -> str:
    """Örnek YAML'ı okur, adresini E2E sunucusuna çevirir."""
    return (ROOT / "examples" / name).read_text(encoding="utf-8").replace("http://127.0.0.1:8000", base)


def api_create_test(base: str, yaml_text: str) -> int:
    """Hazırlık adımı: testi API üzerinden kaydeder (her testte editörle uğraşmamak için)."""
    req = urllib.request.Request(
        base + "/api/tests", data=json.dumps({"yaml": yaml_text}).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)["id"]


def run_from_ui(page: Page, test_id: int) -> None:
    """Test sayfasını açar, Koştur'a basar ve rapor sayfasına gelindiğini doğrular."""
    page.goto(f"/tests/{test_id}")
    page.get_by_role("button", name="▶ Koştur").click()
    expect(page).to_have_url(re.compile(r"/runs/\d+$"))


def summary_badge(page: Page):
    return page.locator(".summary-status .badge")


# --- US-1: Kod yazmadan test tanımlama --------------------------------------

def test_create_test_in_editor(page: Page, platform):
    page.goto("/tests/new")
    editor = page.get_by_label("Test tanımı (YAML)")
    editor.fill(example("demo/giris.yaml", platform).replace("Demo - Başarılı giriş", "E2E - Editörden test"))

    expect(page.locator("#validation")).to_have_text("✓ Geçerli · 8 adım")
    page.get_by_role("button", name="Kaydet").click()

    expect(page.get_by_role("status")).to_have_text("✓ Kaydedildi.")
    expect(page.get_by_role("heading", level=1)).to_have_text("E2E - Editörden test")
    page.get_by_role("link", name="← Testler").click()
    expect(page.get_by_role("link", name="E2E - Editörden test")).to_be_visible()


def test_invalid_test_is_rejected_with_turkish_errors(page: Page):
    page.goto("/tests/new")
    editor = page.get_by_label("Test tanımı (YAML)")
    text = editor.input_value().replace("click: { role: button", "tikla: { role: button")
    editor.fill(text)

    # Canlı doğrulama: kaydetmeden, yazarken
    validation = page.locator("#validation")
    expect(validation).to_contain_text("Test tanımı geçersiz")
    expect(validation).to_contain_text("4. adım: bilinmeyen adım tipi 'tikla'")

    # Yine de kaydetmeye çalışırsa: sunucu reddeder, yazdıkları kaybolmaz
    page.get_by_role("button", name="Kaydet").click()
    expect(page).to_have_url(re.compile(r"/tests/new$"))
    expect(validation).to_contain_text("bilinmeyen adım tipi 'tikla'")
    expect(editor).to_have_value(re.compile("tikla: "))


# --- US-2 / US-3: Koşturma ve rapor -------------------------------------------

def test_passing_run_shows_passed_report(page: Page, platform):
    test_id = api_create_test(platform, example("demo/siparis.yaml", platform))
    run_from_ui(page, test_id)

    # Önce "Sırada"/"Koşuyor"; sayfa kendini yeniledikçe "Geçti" olur.
    expect(summary_badge(page)).to_have_text("Geçti", timeout=RUN_TIMEOUT)
    steps = page.locator("table.steps tbody tr")
    expect(steps).to_have_count(15)
    expect(page.locator("tr.step-failed")).to_have_count(0)
    # Son adım ekran görüntüsü aldı ve sayfada görünüyor
    expect(page.get_by_alt_text("15. adımın ekran görüntüsü")).to_be_visible()


def test_regression_in_v2_is_caught_with_evidence(page: Page, platform):
    test_id = api_create_test(platform, example("demo/siparis-v2.yaml", platform))
    run_from_ui(page, test_id)

    expect(summary_badge(page)).to_have_text("Kaldı", timeout=RUN_TIMEOUT)
    expect(page.get_by_role("alert")).to_contain_text("10. adım (expectText)")
    expect(page.get_by_role("alert")).to_contain_text("1.250 TL")

    failed = page.locator("tr.step-failed")
    expect(failed).to_have_count(1)
    expect(failed).to_contain_text('testId="sepet-toplami"')
    expect(page.locator("tr.step-skipped")).to_have_count(5)

    # Hata anının ekran görüntüsü gerçekten yüklendi mi? (bozuk resim değil)
    shot = page.get_by_alt_text("10. adımın ekran görüntüsü")
    expect(shot).to_be_visible()
    assert shot.evaluate("img => img.naturalWidth") > 0

    # Trace indirilebilir
    with page.expect_download() as download:
        page.get_by_role("link", name="trace.zip indir").click()
    assert download.value.suggested_filename == "trace.zip"


# --- US-4: Koşu geçmişi -------------------------------------------------------

def test_run_history_can_be_filtered_by_status(page: Page, platform):
    test_id = api_create_test(platform, example("demo/siparis-v2.yaml", platform).replace(
        "Sürüm 2.0)", "Sürüm 2.0) - süzgeç"))
    run_from_ui(page, test_id)
    expect(summary_badge(page)).to_have_text("Kaldı", timeout=RUN_TIMEOUT)

    page.goto("/runs")
    page.get_by_label("Durum").select_option(label="Kaldı")
    page.get_by_role("button", name="Süz").click()

    expect(page).to_have_url(re.compile(r"status=failed"))
    badges = page.locator("table tbody .badge")
    expect(badges.first).to_be_visible()
    for text in badges.all_inner_texts():
        assert text == "Kaldı"


# --- Test silme ---------------------------------------------------------------

def test_delete_test_asks_for_confirmation(page: Page, platform):
    test_id = api_create_test(platform, example("demo/giris.yaml", platform).replace(
        "Demo - Başarılı giriş", "E2E - Silinecek test"))
    page.goto(f"/tests/{test_id}")

    page.once("dialog", lambda dialog: dialog.accept())  # "silinsin mi?" sorusuna evet
    page.get_by_role("button", name="Sil").click()

    expect(page).to_have_url(re.compile(r"/$"))
    expect(page.get_by_role("link", name="E2E - Silinecek test")).to_have_count(0)


# --- Platform kendi kendini test ediyor ---------------------------------------

def test_platform_tests_its_own_ui_with_its_own_dsl(page: Page, platform):
    """examples/platform/arayuz.yaml platformun editörünü platformun DSL'iyle sınar.
    Bu YAML'ı worker koşturur; biz de sonucu web arayüzünden okuruz."""
    test_id = api_create_test(platform, example("platform/arayuz.yaml", platform))
    run_from_ui(page, test_id)
    expect(summary_badge(page)).to_have_text("Geçti", timeout=RUN_TIMEOUT)
    expect(page.locator("table.steps tbody tr")).to_have_count(9)


# --- Bonus: görsel regresyon --------------------------------------------------

def test_visual_regression_flow(page: Page, platform):
    """Sunumdaki akış: referans oluştur -> yeni sürüme yönlendir -> fark yakalanır ->
    fark bilinçliyse yeni referans yap -> tekrar koşu geçer."""
    test_id = api_create_test(platform, example("demo/gorsel-sepet.yaml", platform))

    # 1) İlk koşu referansı oluşturur
    run_from_ui(page, test_id)
    expect(summary_badge(page)).to_have_text("Geçti", timeout=RUN_TIMEOUT)
    expect(page.get_by_text("bu görüntü referans olarak kaydedildi")).to_be_visible()

    # 2) Editörde testi Sürüm 2.0'a yönlendir ve koştur
    page.goto(f"/tests/{test_id}")
    editor = page.get_by_label("Test tanımı (YAML)")
    editor.fill(editor.input_value().replace("/demo\n", "/demo-v2\n"))
    page.get_by_role("button", name="Kaydet").click()
    expect(page.get_by_role("status")).to_have_text("✓ Kaydedildi.")
    page.get_by_role("button", name="▶ Koştur").click()

    expect(summary_badge(page)).to_have_text("Kaldı", timeout=RUN_TIMEOUT)
    expect(page.locator("tr.step-failed")).to_contain_text("görsel fark")
    for label in ("Referans", "Bu koşu", "Fark (kırmızı)"):
        img = page.get_by_alt_text(f"9. adım: {label}")
        expect(img).to_be_visible()
        assert img.evaluate("img => img.naturalWidth") > 0

    # 3) Fark bilinçli: yeni referans yap, tekrar koştur -> geçer
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Bu görüntüyü yeni referans yap").click()
    expect(page.get_by_role("status")).to_contain_text("yeni referans olarak kaydedildi")
    page.get_by_role("button", name="▶ Tekrar koştur").click()
    expect(summary_badge(page)).to_have_text("Geçti", timeout=RUN_TIMEOUT)
    expect(page.get_by_text("Referansla fark: %0.000 (0 piksel)")).to_be_visible()
