"""DSL (YAML test formatı) doğrulamasının birim testleri. Tarayıcı açmaz, hızlı çalışır."""

from pathlib import Path

import pytest

from engine.dsl import DslError, LocatorSpec, ValueLocatorSpec, load_test, parse_test

HEADER = """
name: Deneme
baseUrl: https://www.saucedemo.com
steps:
"""


def errors_of(yaml_text: str) -> str:
    """Geçersiz YAML'ı doğrular ve tüm hata mesajlarını tek metin olarak döndürür."""
    with pytest.raises(DslError) as info:
        parse_test(yaml_text)
    return "\n".join(info.value.errors)


# --- Geçerli dosyalar -------------------------------------------------------

def test_valid_test_is_parsed():
    test = parse_test(HEADER + """
  - goto: /
  - fill: { label: Username, value: standard_user }
  - fill: { testId: password, value: secret_sauce }
  - click: { role: button, name: Login }
  - expectUrl: /inventory.html
  - expectVisible: { text: Products }
  - expectText: { css: .title, value: Products }
  - screenshot: urun-listesi
""")
    assert test.name == "Deneme"
    assert test.base_url == "https://www.saucedemo.com"
    assert [s.kind for s in test.steps] == [
        "goto", "fill", "fill", "click", "expectUrl", "expectVisible", "expectText", "screenshot",
    ]
    assert [s.number for s in test.steps] == list(range(1, 9))
    assert test.steps[0].args == "/"
    assert isinstance(test.steps[1].args, ValueLocatorSpec)
    assert test.steps[1].args.value == "standard_user"
    assert isinstance(test.steps[3].args, LocatorSpec)
    assert test.steps[3].args.role == "button" and test.steps[3].args.name == "Login"


def test_defaults_are_applied():
    test = parse_test(HEADER + "  - goto: /\n")
    assert test.timeout == 60_000
    assert test.step_timeout == 10_000
    assert test.test_id_attribute == "data-testid"


def test_custom_timeouts_and_step_timeout():
    test = parse_test("""
name: Zaman aşımı
baseUrl: https://example.com
timeout: 30000
stepTimeout: 2000
steps:
  - click: { css: "#btn", timeout: 500 }
""")
    assert test.timeout == 30_000
    assert test.step_timeout == 2_000
    assert test.steps[0].args.timeout == 500


def test_fail_on_page_errors_option():
    assert parse_test(HEADER + "  - goto: /\n").fail_on_page_errors is False
    test = parse_test(HEADER.replace("steps:", "failOnPageErrors: true\nsteps:") + "  - goto: /\n")
    assert test.fail_on_page_errors is True
    msg = errors_of(HEADER.replace("steps:", "failOnPageErrors: belki\nsteps:") + "  - goto: /\n")
    assert "failOnPageErrors" in msg


def test_retries_option_and_limits():
    assert parse_test(HEADER + "  - goto: /\n").retries == 0
    assert parse_test(HEADER.replace("steps:", "retries: 3\nsteps:") + "  - goto: /\n").retries == 3
    msg = errors_of(HEADER.replace("steps:", "retries: 6\nsteps:") + "  - goto: /\n")
    assert "'retries' 5 değerinden büyük olamaz" in msg
    msg = errors_of(HEADER.replace("steps:", "retries: -1\nsteps:") + "  - goto: /\n")
    assert "'retries' 0 değerinden küçük olamaz" in msg


def test_numeric_value_becomes_text():
    test = parse_test(HEADER + "  - fill: { css: '#zip', value: 34000 }\n")
    assert test.steps[0].args.value == "34000"


def test_example_files_are_valid():
    examples = sorted(Path("examples").glob("*.yaml"))
    assert len(examples) >= 3
    for path in examples:
        load_test(path)  # hata fırlatmamalı


# --- Adım hataları ----------------------------------------------------------

def test_unknown_step_type():
    msg = errors_of(HEADER + "  - goto: /\n  - tikla: { text: Login }\n")
    assert "2. adım" in msg
    assert "bilinmeyen adım tipi 'tikla'" in msg


def test_missing_locator():
    msg = errors_of(HEADER + "  - click: { timeout: 1000 }\n")
    assert "1. adım (click)" in msg
    assert "locator gerekli" in msg


def test_two_locators_at_once():
    msg = errors_of(HEADER + "  - click: { text: Login, css: '#login' }\n")
    assert "1. adım (click)" in msg
    assert "birden fazla" in msg
    assert "text" in msg and "css" in msg


def test_name_without_role():
    msg = errors_of(HEADER + "  - click: { text: Login, name: Login }\n")
    assert "'name' alanı sadece 'role'" in msg


def test_fill_without_value():
    msg = errors_of(HEADER + "  - fill: { label: Username }\n")
    assert "1. adım (fill)" in msg
    assert "'value' alanı zorunlu" in msg


def test_unknown_field_in_step():
    msg = errors_of(HEADER + "  - click: { text: Login, color: red }\n")
    assert "bilinmeyen alan 'color'" in msg


def test_unquoted_comma_gives_hint():
    msg = errors_of(HEADER + "  - fill: { label: Adres, value: Cad. No 1, Ankara }\n")
    assert "bilinmeyen alan 'Ankara'" in msg
    assert "tırnak içine" in msg


def test_step_with_two_types():
    msg = errors_of(HEADER + "  - goto: /\n    click: { text: Login }\n")
    assert "1. adım" in msg
    assert "tek bir adım tipi" in msg


def test_string_step_needs_text():
    msg = errors_of(HEADER + "  - goto: { url: / }\n")
    assert "1. adım (goto)" in msg
    assert "metin bekleniyor" in msg


def test_locator_step_needs_dict():
    msg = errors_of(HEADER + "  - click: Login\n")
    assert "1. adım (click)" in msg
    assert "sözlük bekleniyor" in msg


def test_all_step_errors_are_reported_together():
    msg = errors_of(HEADER + "  - foo: bar\n  - goto: /\n  - click: {}\n")
    assert "1. adım" in msg
    assert "3. adım (click)" in msg


# --- Kök alan hataları ------------------------------------------------------

def test_missing_base_url():
    msg = errors_of("name: X\nsteps:\n  - goto: /\n")
    assert "'baseUrl' alanı zorunlu" in msg


def test_invalid_base_url():
    msg = errors_of("name: X\nbaseUrl: www.site.com\nsteps:\n  - goto: /\n")
    assert "http:// veya https://" in msg


def test_empty_steps():
    msg = errors_of("name: X\nbaseUrl: https://a.com\nsteps: []\n")
    assert "boş olamaz" in msg


def test_unknown_root_field():
    msg = errors_of(HEADER.replace("steps:", "browser: firefox\nsteps:") + "  - goto: /\n")
    assert "bilinmeyen alan 'browser'" in msg


def test_negative_timeout():
    msg = errors_of(HEADER.replace("steps:", "timeout: -5\nsteps:") + "  - goto: /\n")
    assert "'timeout' sıfırdan büyük" in msg


def test_yaml_syntax_error_has_line_number():
    msg = errors_of("name: X\nbaseUrl: https://a.com\nsteps:\n  - click: { text: Login\n")
    assert "YAML sözdizimi hatası" in msg
    assert "satır" in msg


def test_not_a_mapping():
    msg = errors_of("- goto: /\n")
    assert "name, baseUrl ve steps" in msg


def test_missing_file():
    with pytest.raises(DslError) as info:
        load_test("yok/boyle-bir-dosya.yaml")
    assert "dosya okunamadı" in info.value.errors[0]


# --- Veri odaklı testler (B3) ------------------------------------------------

DATA_TEST = """
name: Giriş
baseUrl: https://a.com
data:
  - { kullanici: demo, sifre: 123 }
  - { kullanici: kilitli, sifre: }
steps:
  - goto: /giris/${kullanici}
  - fill: { label: Kullanıcı adı, value: "${kullanici}" }
  - fill: { label: Şifre, value: "${sifre}" }
  - screenshot: sonuc-${kullanici}
"""


def test_data_rows_are_expanded_with_placeholders_filled():
    test = parse_test(DATA_TEST)
    assert test.data == [{"kullanici": "demo", "sifre": "123"}, {"kullanici": "kilitli", "sifre": ""}]
    first, second = test.expand_rows()
    assert first.name == "Giriş [1. satır]" and second.name == "Giriş [2. satır]"
    assert first.data_row == {"kullanici": "demo", "sifre": "123"}
    assert first.data == [] and test.data  # kopyalar tekrar açılmaz; asıl test değişmez
    assert first.steps[0].args == "/giris/demo"
    assert first.steps[1].args.value == "demo" and first.steps[1].args.label == "Kullanıcı adı"
    assert second.steps[2].args.value == ""  # boş değer -> boş metin
    assert second.steps[3].args == "sonuc-kilitli"
    assert test.steps[1].args.value == "${kullanici}"  # şablon olduğu gibi kalır


def test_placeholder_missing_in_a_row():
    msg = errors_of(DATA_TEST.replace("  - { kullanici: kilitli, sifre: }", "  - { kullanici: kilitli }"))
    assert "3. adım (fill): '${sifre}' veri tablosunun 2. satırında yok" in msg


def test_placeholder_without_data_table():
    msg = errors_of(HEADER + '  - fill: { label: A, value: "${kullanici}" }\n')
    assert "'${kullanici}' kullanılmış ama 'data' tablosu tanımlı değil" in msg


def test_empty_data_table_and_bad_values():
    assert "en az bir satır" in errors_of(HEADER.replace("steps:", "data: []\nsteps:") + "  - goto: /\n")
    nested = HEADER.replace("steps:", "data:\n  - { a: [1, 2] }\nsteps:") + "  - goto: /\n"
    assert "'a' tek bir değer olmalı" in errors_of(nested)


def test_unquoted_placeholder_in_braces_gives_hint():
    msg = errors_of(DATA_TEST.replace('value: "${kullanici}"', "value: ${kullanici}"))
    assert "YAML sözdizimi hatası" in msg
    assert "değeri tırnağa alın" in msg
