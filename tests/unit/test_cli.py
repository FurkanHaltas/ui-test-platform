"""CLI'ın çıkış kodlarının testleri (US-5). `validate` komutu tarayıcı açmaz."""

from engine.cli import main


def test_validate_valid_folder_returns_0(capsys):
    assert main(["validate", "examples/"]) == 0
    assert "test dosyası geçerli" in capsys.readouterr().out


def test_validate_invalid_file_returns_2_and_lists_errors(capsys):
    assert main(["validate", "examples/gecersiz/hatali-format.yaml"]) == 2
    out = capsys.readouterr().out
    assert "bilinmeyen adım tipi 'tikla'" in out
    assert "Test koşturulmadı" in out


def test_run_with_invalid_file_does_not_start_browser(capsys):
    # Geçerli ve geçersiz dosya birlikte verilirse hiçbiri koşmaz, çıkış kodu 2 olur.
    assert main(["run", "examples/login.yaml", "examples/gecersiz/hatali-format.yaml"]) == 2
    assert "geçti" not in capsys.readouterr().out


def test_empty_folder_returns_2(tmp_path, capsys):
    assert main(["validate", str(tmp_path)]) == 2
    assert "bulunamadı" in capsys.readouterr().out
