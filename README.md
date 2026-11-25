# Otomatik UI Test Platformu

BİLS403 Yazılım Mühendisliği final projesi. Web uygulamalarının uçtan uca (E2E) testlerini **kod yazmadan, YAML ile** tanımlayıp gerçek bir tarayıcıda (Playwright + Chromium) çalıştıran platform.

> Durum: **Aşama 1 — Test motoru** tamam. API, web arayüzü ve CI sonraki aşamalarda (bkz. [ROADMAP.md](ROADMAP.md)).

## Kurulum (Windows / PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
```

> PowerShell betik çalıştırmayı engellerse bir kez şunu çalıştırın:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Kullanım

```powershell
python -m engine run examples/login.yaml          # tek test
python -m engine run examples/                    # klasördeki tüm testler
python -m engine run examples/login.yaml --headed --channel chrome   # tarayıcı görünür
python -m engine validate examples/gecersiz/      # sadece YAML doğrulama
python -m pytest                                  # birim testleri
```

Her koşunun çıktısı `artifacts/<tarih-saat>_<test-adı>/` altına yazılır: `result.json` ve ekran görüntüleri. Kalan testlerde ayrıca `trace.zip` olur, şu komutla açılır:

```powershell
python -m playwright show-trace artifacts\<klasör>\trace.zip
```

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

**Locator'lar** (her adımda tam olarak biri): `role` (+`name`), `label`, `testId`, `text`, `css`. Locator'lı adımlara `timeout: 3000` eklenerek o adıma özel süre verilebilir.

## Klasörler

| Klasör | İçerik |
|--------|--------|
| `engine/` | Test motoru (`dsl`, `locators`, `steps`, `runner`, `results`, `cli`) |
| `examples/` | saucedemo.com örnek testleri (biri bilerek kalır), `gecersiz/` hatalı format örneği |
| `tests/unit/` | Birim testleri |
| `docs/` | [Tasarım kararları](docs/kararlar.md), [UML diyagramları](docs/uml/) |
| `api/`, `worker/`, `web/`, `tests/e2e/` | Sonraki aşamalar |
