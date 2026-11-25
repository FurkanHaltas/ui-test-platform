"""Motorun tarayıcı gerektirmeyen yardımcı fonksiyonlarının birim testleri."""

from pathlib import Path

from engine.dsl import parse_test
from engine.runner import short_error, slugify
from engine.steps import ClickStep, GotoStep, ScreenshotStep, build_steps, resolve_url


def test_resolve_url_joins_relative_paths():
    assert resolve_url("https://a.com", "/x.html") == "https://a.com/x.html"
    assert resolve_url("https://a.com/", "x.html") == "https://a.com/x.html"
    assert resolve_url("https://a.com/app", "/login") == "https://a.com/app/login"


def test_resolve_url_keeps_absolute_urls():
    assert resolve_url("https://a.com", "https://b.com/y") == "https://b.com/y"


def test_slugify_turkish_names():
    assert slugify("Başarılı giriş") == "basarili-giris"
    assert slugify("Ürünü sepete ekleme!") == "urunu-sepete-ekleme"
    assert slugify("???") == "test"


def test_short_error_drops_call_log():
    e = Exception("Locator.click: Timeout 3000ms exceeded.\nCall log:\n  - waiting for ...")
    msg = short_error(e)
    assert "Call log" not in msg
    assert msg.startswith("zaman aşımı")


def test_build_steps_creates_command_objects():
    test = parse_test("""
name: X
baseUrl: https://a.com
steps:
  - goto: /
  - click: { text: Login }
  - screenshot: ana-sayfa
""")
    steps = build_steps(test, Path("out"))
    assert [type(s) for s in steps] == [GotoStep, ClickStep, ScreenshotStep]
    assert steps[0].url == "https://a.com/"
    assert steps[2].path == Path("out") / "ana-sayfa.png"
    assert steps[1].describe() == 'click text="Login"'
