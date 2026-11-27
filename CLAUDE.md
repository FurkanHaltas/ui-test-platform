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
- `api/` FastAPI + `db.py` (SQLite), `worker/` kuyruk işleyici, `tests/integration/` worker testi
- `web/` Jinja2 web arayüzü (`routes.py`, `templates/`, `static/`), `demo_site/` yerel demo mağaza (/demo, /demo-v2)
- `tests/e2e/` sonraki aşama
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

## Rapor (dokümantasyon) kuralları
- Teslim dokümanının malzemesi `rapor/` klasöründe; hocanın şablonuna göre durum tablosu `rapor/README.md`'de. Teknik belgeler `docs/` altında kalır.
- Bir hata bulunup giderilince `rapor/hata-kaydi.md`'ye ekle (belirti, kök neden, çözüm, doğrulama).
- Yeni bir kaynak (kütüphane belgesi, makale) kullanılınca `rapor/kaynakca.md`'ye ekle.
- Bir gereksinim gerçekleşince `rapor/02-gereksinim-analizi.md`'deki durumunu ve izlenebilirlik matrisini güncelle; yeni kabul kriteri yazılırsa onu doğrulayan testi de yaz.
- Her aşama sonunda `rapor/README.md` durum tablosunu ve ROADMAP'teki doküman görevlerini güncelle.

## Komutlar
```powershell
.venv\Scripts\Activate.ps1
python -m engine run examples/login.yaml          # tek test
python -m engine run examples/ --headed           # klasördeki tüm testler, tarayıcı görünür
python -m pytest                                  # birim + entegrasyon testleri
uvicorn api.main:app --reload                     # web arayüzü http://127.0.0.1:8000 , API /docs
python -m worker                                  # kuyruk işleyici (ayrı terminal)
python -m api.seed                                # örnek testleri DB'ye yükle
```

## Aşama 2 notları
- `api/db.py` düz SQL + sqlite3 (ORM yok). `runs` tablosundaki `queued` satırlar = iş kuyruğu.
- Testler geçici DB kullanır: `tests/conftest.py` içindeki `conn` fixture'ı `UITP_DB`'yi ayarlar.
- Motor dosya yollarını `as_posix()` ile yazar; API bunları `/artifacts/...` URL'lerine çevirir.
- Bu makinede indirilen Chromium görünür modda açılmıyor: `--headed` için `--channel chrome` kullan.

## Aşama 3 notları
- Web sayfaları `api/db.py`'yi doğrudan kullanır; doğrulama her yerde `engine.dsl.parse_test`. Formlar POST → 303 (PRG).
- Demo sitesi `demo_site/`, `/demo` (1.0) ve `/demo-v2` (2.0, sepet toplamı bilerek hatalı) altında aynı API sunucusundan yayınlanır. Örnekleri `examples/demo/`.
- `goto` `wait_until="domcontentloaded"` kullanır (yavaş dış sitelerde gereksiz zaman aşımını önler).
- Önizleme: `~/.claude/launch.json` içinde `ui-test-api` kaydı. Worker'ı ayrıca başlat; motor kodu değişince worker'ı yeniden başlat.

## Aşama 4 notları
- `python -m pytest` = birim + entegrasyon + E2E (~1,5 dk). Raporlar `reports/` (gitignore). Sadece hızlı: `python -m pytest tests/unit -o addopts=""`.
- E2E (`tests/e2e/`): conftest sunucu + worker'ı geçici klasörde ayrı süreç olarak başlatır. pytest-playwright yüzünden E2E her zaman en sona sıralanır (`tests/conftest.py`, H-11); E2E içinde motoru aynı süreçte çağırma, worker'a koşturt.
- CI: `.github/workflows/ci.yml` (Ubuntu, dış site yok). Özet: `.github/scripts/test_ozeti.py`.
- Görsel regresyon: `expectScreenshot`, `engine/visual.py` (Pillow), referanslar `data/baselines/<slug>/`. Web'de "yeni referans yap" = `POST /runs/{id}/steps/{n}/accept`.

## Depo
- Uzak depo: https://github.com/FurkanHaltas/ui-test-platform (herkese açık), dal `main`. Her push CI'ı tetikler.
- `Proje Başlama Promptu.txt` sadece yerelde kalır (`.gitignore`'da); git geçmişinden de çıkarıldı. Asla commit'leme.

## Bonus notları
- B1 (sayfa hatası yakalama): `engine/page_errors.py` (PageErrorCollector), `RunResult.page_errors`, DSL `failOnPageErrors`. Demo 2.0 ürünler sayfasında bilinçli 3 hata (`demo_site/app.js` → addV2PageErrors); 1.0'da 0 hata olmalı (test_page_errors).
