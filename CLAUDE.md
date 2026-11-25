# CLAUDE.md — Otomatik UI Test Platformu

## Proje bağlamı
- Ders: BİLS403 Yazılım Mühendisliği (bilgisayar mühendisliği 4. sınıf), final projesi.
- Konu: Otomatik UI Test Platformu — web uygulaması akışlarının uçtan uca (E2E) otomatik sınanması.
- MVP kapsamı: 1) test tanımı, 2) tarayıcı otomasyonu, 3) rapor.
- Teslim: **28 Aralık 2026** — rapor, sunum, UML diyagramları, canlı demo.
- Fikir: Kullanıcı testleri kod yazmadan YAML ile adım adım tanımlar; sistem bunları Playwright ile gerçek tarayıcıda uygular, sonucu kaydeder ve raporlar.
- Geliştirme ortamı: Windows 11, Python 3.12, `.venv` sanal ortamı.

## Teknoloji yığını
- Python 3.11+, venv
- Playwright (Python, **senkron API**), şimdilik sadece Chromium
- Pydantic v2 (DSL doğrulama), PyYAML
- Sonraki aşamalar: FastAPI, SQLite, Jinja2, pytest-playwright, GitHub Actions

## Mimari (genel resim)
Web arayüzü → API (FastAPI) → veritabanı + iş kuyruğu (MVP'de DB'deki `queued` satırları) → worker → test motoru (Playwright) → hedef site.
Ekran görüntüleri ve trace dosyaları `artifacts/` altına yazılır.

## Klasörler
- `engine/` test motoru: `dsl.py`, `locators.py`, `steps.py`, `runner.py`, `results.py`, `cli.py`
- `api/`, `worker/`, `web/`, `tests/e2e/` sonraki aşamalar
- `examples/` örnek YAML testleri
- `tests/unit/` motorun birim testleri
- `docs/` `kararlar.md` (tasarım kararları, rapor için) ve `uml/` (Mermaid diyagramları)
- `artifacts/` koşu çıktıları (git'e girmez)

## DSL v1 özeti
- Kök alanlar: `name`, `baseUrl`, `steps` (opsiyonel: `timeout` ms, `stepTimeout` ms)
- Adım tipleri: `goto`, `click`, `fill`, `expectVisible`, `expectText`, `expectUrl`, `screenshot`
- Locator öncelik sırası: `role`+`name`, `label`, `testId`, `text`, `css`. Her adımda **tam olarak bir** locator türü.
- Hatalı YAML'da hangi adımda ne hata olduğunu söyleyen Türkçe mesaj verilir.

## Çalışma kuralları
- Kod, değişken ve fonksiyon isimleri **İngilizce**; yorumlar, açıklamalar ve hata mesajları **Türkçe**.
- Basit ve okunabilir kod. Savunmada her satır açıklanabilmeli. Gereksiz soyutlama yok.
- Her anlamlı adımdan sonra açıklayıcı mesajla git commit.
- Bir aşama bitince DUR; sonraki aşamaya kendiliğinden geçme.
- Aşama sonunda kullanıcıya Türkçe ve basit dille anlat: ne yapıldı, dosyalar ne işe yarıyor, bir YAML adımı nasıl Playwright komutuna dönüşüyor, nasıl çalıştırılıp test edilir. Teknik terimleri kısaca açıkla.
- Playwright'ın kendi bekleme mekanizmasını kullan; sabit `sleep` kullanma.
- **MVP (aşama 1-3) tamamlanınca kullanıcıya ROADMAP.md'deki bonusları hatırlat.**

## Komutlar
```powershell
.venv\Scripts\Activate.ps1
python -m engine run examples/login.yaml          # tek test
python -m engine run examples/ --headed           # klasördeki tüm testler, tarayıcı görünür
python -m pytest tests/unit                       # birim testleri
```
