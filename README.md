# Otomatik UI Test Platformu

BİLS403 Yazılım Mühendisliği final projesi. Web uygulamalarının uçtan uca (E2E) testlerini **kod yazmadan, YAML ile** tanımlayıp gerçek bir tarayıcıda (Playwright + Chromium) çalıştıran platform.

> Durum: **MVP tamam** (Aşama 1–3). Aşama 4: platformun kendi E2E testleri, GitHub Actions iş akışı ve görsel regresyon (bonus) hazır; GitHub'a yükleme bekliyor (bkz. [ROADMAP.md](ROADMAP.md)).

```
Tarayıcı ──▶ Web arayüzü ┐
                         ├─▶ SQLite (tests, runs = kuyruk) ◀── Worker ──▶ Test motoru ──▶ Chromium ──▶ Hedef site
İstemci  ──▶ JSON API  ──┘                                                     │
             /artifacts (ekran görüntüleri, trace) ◀───────────────────────────┘
```

## Kurulum (Windows / PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
```

> PowerShell betik çalıştırmayı engellerse bir kez şunu çalıştırın:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Hızlı başlangıç (web arayüzü + demo)

İki ayrı terminal açın, ikisinde de önce `.venv\Scripts\Activate.ps1` çalıştırın.

```powershell
uvicorn api.main:app --reload
```
```powershell
python -m worker
```

İlk seferde örnek testleri yükleyin:

```powershell
python -m api.seed
```

Sonra tarayıcıda <http://127.0.0.1:8000> adresini açın.

| Sayfa | Ne yapılır |
|-------|-----------|
| **Testler** (`/`) | Testleri listele, son durumlarını gör, tek tek ya da hepsini koştur |
| **Test editörü** (`/tests/{id}`) | YAML yaz; yazarken canlı doğrulama, Ctrl+S ile kaydet |
| **Koşular** (`/runs`) | Koşu geçmişi, teste ve duruma göre süzme |
| **Rapor** (`/runs/{id}`) | Adım adım sonuç, kalan adımın ekran görüntüsü, trace indirme |
| **Demo site** (`/demo/`, `/demo-v2/`) | Testlerin koşturulduğu yerel mağaza (internet gerekmez) |
| **API** (`/docs`) | JSON API belgeleri ve deneme ekranı |

### Demo sitesi (Mini Market)
İnternete bağımlı olmadan canlı demo yapmak için `demo_site/` klasöründe küçük bir mağaza var. Aynı sunucu bunu iki adreste yayınlar:
- `/demo/` — **Sürüm 1.0**, doğru çalışır.
- `/demo-v2/` — **Sürüm 2.0**, sepette birden fazla ürün varken toplamı **bilerek yanlış** hesaplar.

Örnek testler `examples/demo/` altında. "Demo - Sipariş akışı (Sürüm 1.0)" geçer; aynı test Sürüm 2.0'a karşı 10. adımda (sepet toplamı) kalır.
Demo hesapları: `demo` / `demo123`, kilitli hesap: `kilitli` / `demo123`.

## Komut satırı (CLI)

```powershell
python -m engine run examples/login.yaml          # tek test
python -m engine run examples/                    # klasördeki tüm testler
python -m engine run examples/login.yaml --headed --channel chrome   # tarayıcı görünür
python -m engine validate examples/gecersiz/      # sadece YAML doğrulama
python -m engine run x.yaml --update-baselines    # görsel referansları yeniden oluştur
```

Her koşunun çıktısı `artifacts/<tarih-saat>_<test-adı>/` altına yazılır: `result.json` ve ekran görüntüleri. Kalan testlerde ayrıca `trace.zip` olur, şu komutla açılır:

```powershell
python -m playwright show-trace artifacts\<klasör>\trace.zip
```

## JSON API

API belgeleri ve deneme ekranı: <http://127.0.0.1:8000/docs>

| Uç nokta | Görevi |
|----------|--------|
| `GET /api/health` | Sağlık durumu ve kuyruktaki iş sayısı |
| `POST /api/validate` | YAML'ı kaydetmeden doğrula |
| `GET/POST /api/tests` | Testleri listele / yeni test kaydet (`{"yaml": "..."}`) |
| `GET/PUT/DELETE /api/tests/{id}` | Tek test |
| `POST /api/tests/{id}/runs` | Testi kuyruğa al (**202**) |
| `GET /api/runs?test_id=&status=` | Koşu listesi |
| `GET /api/runs/{id}` | Koşu ayrıntısı: adımlar, `screenshot_url`, `trace_url` |
| `GET /artifacts/...` | Ekran görüntüsü ve trace dosyaları |

Koşu durumları: `queued` → `running` → `passed` / `failed` (test bir hata buldu) / `error` (test çalıştırılamadı).

Veritabanı: `data/platform.db` (`UITP_DB` ortam değişkeniyle değiştirilebilir). Worker'a `--once` verilirse kuyruğu bitirip çıkar; `--channel chrome` ile kurulu Chrome'u kullanır.

## Platformun kendi testleri

```powershell
python -m pytest
```

86 test: 66 birim (tarayıcısız, ~2 sn), 12 entegrasyon ve 8 E2E (gerçek Chromium, internet gerekmez; toplam ~1,5 dk). E2E testleri sunucuyu ve worker'ı geçici bir klasörde kendileri başlatır; `data/platform.db`'ye dokunmaz.
Her çalıştırma `reports/test-raporu.html` (tarayıcıda açın) ve `reports/junit.xml` üretir. Ayrıntılar: [rapor/05-yazilim-testleri.md](rapor/05-yazilim-testleri.md).

**CI:** `.github/workflows/ci.yml` her push ve pull request'te aynı testleri GitHub Actions'ta (Ubuntu) koşturur.

## Görsel regresyon

`expectScreenshot: ad` adımı sayfanın görüntüsünü testin referans görüntüsüyle karşılaştırır. İlk koşuda referans `data/baselines/<test-adı>/` altına kaydedilir. Sonraki koşularda değişen pikseller %0,01'i aşarsa adım kalır ve raporda referans / bu koşu / fark görüntüleri yan yana görünür. Fark bilinçliyse rapordaki **"Bu görüntüyü yeni referans yap"** butonunu kullanın. Örnek: `examples/demo/gorsel-sepet.yaml`.

## Test formatı (DSL v1)

```yaml
name: Başarılı giriş
baseUrl: https://www.saucedemo.com
testIdAttribute: data-test   # opsiyonel, varsayılan data-testid
timeout: 60000               # opsiyonel, testin tamamı (ms)
stepTimeout: 10000           # opsiyonel, adım başına (ms)
steps:
  - goto: /
  - fill: { label: Username, value: standard_user }
  - fill: { testId: password, value: secret_sauce }
  - click: { role: button, name: Login }
  - expectUrl: /inventory.html
  - expectVisible: { text: Products }
  - expectText: { testId: title, value: Products }
  - screenshot: urun-listesi
```

| Adım | Ne yapar | Playwright karşılığı |
|------|----------|----------------------|
| `goto: /yol` | Sayfaya git | `page.goto(url)` |
| `click: {locator}` | Tıkla | `locator.click()` |
| `fill: {locator, value}` | Kutuya yaz | `locator.fill(value)` |
| `expectVisible: {locator}` | Görünür olmalı | `expect(locator).to_be_visible()` |
| `expectText: {locator, value}` | Metni tam olarak bu olmalı | `expect(locator).to_have_text(value)` |
| `expectUrl: /yol` | Adres bu olmalı | `expect(page).to_have_url(url)` |
| `screenshot: ad` | Ekran görüntüsü al | `page.screenshot(path)` |
| `expectScreenshot: ad` | Görüntü referansla aynı olmalı (görsel regresyon) | `page.screenshot` + Pillow ile piksel karşılaştırma |

**Locator'lar** (her adımda tam olarak biri): `role` (+`name`), `label`, `testId`, `text`, `css`. Locator'lı adımlara `timeout: 3000` eklenerek o adıma özel süre verilebilir.

## Klasörler

| Klasör | İçerik |
|--------|--------|
| `engine/` | Test motoru (`dsl`, `locators`, `steps`, `runner`, `results`, `cli`) |
| `examples/` | saucedemo.com örnek testleri (biri bilerek kalır), `gecersiz/` hatalı format örneği |
| `api/` | FastAPI uygulaması (`main.py`), veritabanı katmanı (`db.py`), modeller (`schemas.py`), `seed.py` |
| `worker/` | Kuyruk işleyici (`python -m worker`) |
| `tests/unit/` | Birim testleri (DSL, veritabanı, API) |
| `web/` | Web arayüzü: `routes.py`, `templates/` (Jinja2), `static/` (CSS, editör betiği) |
| `demo_site/` | Yerel demo mağaza (HTML + JS, sunucusuz) |
| `tests/integration/` | Worker ve demo sitesi testleri (gerçek Chromium, yerel sayfalara karşı) |
| `docs/` | [Tasarım kararları](docs/kararlar.md), [UML diyagramları](docs/uml/) |
| `rapor/` | Teslim dokümanının bölümleri, hata kaydı, kaynakça ([durum tablosu](rapor/README.md)) |
| `data/` | SQLite veritabanı (git'e girmez) |
| `tests/e2e/` | Sonraki aşama |
