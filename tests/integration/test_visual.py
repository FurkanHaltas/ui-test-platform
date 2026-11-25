"""Görsel regresyon testleri.

Birinci kısım tarayıcı açmaz: karşılaştırma fonksiyonunu küçük, elle çizilmiş görüntülerle sınar.
İkinci kısım gerçek Chromium ile demo sitesine karşı çalışır: Sürüm 1.0 referans oluşturur,
aynı test Sürüm 2.0'da yanlış toplamı görsel farktan yakalar.
"""

from pathlib import Path

from PIL import Image, ImageDraw

from engine.dsl import parse_test
from engine.runner import run_tests
from engine.visual import compare_images
from tests.integration.test_demo_site import site  # noqa: F401  (yerel demo sunucusu fixture'ı)


def image(path: Path, square_color=None) -> Path:
    img = Image.new("RGB", (200, 100), "white")
    if square_color:
        ImageDraw.Draw(img).rectangle([10, 10, 19, 19], fill=square_color)  # 10x10 = 100 piksel
    img.save(path)
    return path


# --- Karşılaştırma fonksiyonu (tarayıcısız) -----------------------------------

def test_identical_images_have_no_difference(tmp_path):
    a, b = image(tmp_path / "a.png"), image(tmp_path / "b.png")
    result = compare_images(a, b, tmp_path / "fark.png")
    assert result.changed_pixels == 0 and result.passed


def test_changed_area_is_counted_and_marked_red(tmp_path):
    a, b = image(tmp_path / "a.png"), image(tmp_path / "b.png", square_color="black")
    result = compare_images(a, b, tmp_path / "fark.png")
    assert result.changed_pixels == 100
    assert result.percent == 100 * 100 / (200 * 100)  # %0,5
    assert not result.passed
    diff = Image.open(tmp_path / "fark.png").convert("RGB")
    assert diff.getpixel((15, 15)) == (230, 20, 20)  # değişen piksel kırmızı
    assert diff.getpixel((100, 50)) != (230, 20, 20)  # değişmeyen piksel kırmızı değil


def test_tiny_color_noise_is_ignored(tmp_path):
    a = image(tmp_path / "a.png")
    b = image(tmp_path / "b.png", square_color=(250, 250, 250))  # beyazdan 5 birim farklı
    assert compare_images(a, b, tmp_path / "fark.png").changed_pixels == 0


def test_different_size_fails(tmp_path):
    a = image(tmp_path / "a.png")
    Image.new("RGB", (300, 100), "white").save(tmp_path / "b.png")
    result = compare_images(a, tmp_path / "b.png", tmp_path / "fark.png")
    assert not result.same_size and not result.passed


# --- Gerçek tarayıcıyla demo sitesi --------------------------------------------

def load(site_url: str, version: str):
    text = Path("examples/demo/gorsel-sepet.yaml").read_text(encoding="utf-8")
    text = text.replace("http://127.0.0.1:8000/demo", f"{site_url}/{version}")
    return parse_test(text, source="gorsel-sepet.yaml")


def test_visual_regression_on_demo_site(site, tmp_path):  # noqa: F811
    baselines = tmp_path / "baselines"
    artifacts = tmp_path / "artifacts"

    # 1) İlk koşu: referans yok -> oluşturulur, geçer
    [first] = run_tests([load(site, "demo")], artifacts_dir=artifacts, baselines_dir=baselines)
    assert first.status == "passed", first.error
    step = first.steps[-1]
    assert "referans olarak kaydedildi" in step.note
    assert Path(step.baseline_source).exists()

    # 2) Aynı sürüm tekrar: fark yok, geçer
    [second] = run_tests([load(site, "demo")], artifacts_dir=artifacts, baselines_dir=baselines)
    assert second.status == "passed", second.error
    assert second.steps[-1].note == "Referansla fark: %0.000 (0 piksel)"

    # 3) Sürüm 2.0: toplam yanlış -> görsel fark yakalanır
    [third] = run_tests([load(site, "demo-v2")], artifacts_dir=artifacts, baselines_dir=baselines)
    assert third.status == "failed"
    step = third.steps[-1]
    assert step.status == "failed"
    assert step.error.startswith("görsel fark")
    for path in (step.screenshot, step.baseline, step.diff):
        assert Path(path).exists()
    print("\nSürüm 2.0 görsel farkı:", step.note)  # pytest -s ile görülebilir


def test_update_baselines_replaces_reference(site, tmp_path):  # noqa: F811
    baselines = tmp_path / "baselines"
    run_tests([load(site, "demo")], artifacts_dir=tmp_path, baselines_dir=baselines)
    # 2.0 görüntüsünü bilerek yeni referans yap: geçer ve sonraki 2.0 koşusu da geçer
    [updated] = run_tests([load(site, "demo-v2")], artifacts_dir=tmp_path, baselines_dir=baselines,
                          update_baselines=True)
    assert updated.status == "passed" and updated.steps[-1].note == "Referans görüntü güncellendi."
    [again] = run_tests([load(site, "demo-v2")], artifacts_dir=tmp_path, baselines_dir=baselines)
    assert again.status == "passed", again.error
