# 5. Yazılım Testleri

## 5.1 Test stratejisi

Platformun kendisi bir test aracı olduğu için iki ayrı "test" kavramı var:
- **Platformun koşturduğu testler:** Kullanıcının YAML ile yazdığı, hedef sitelere karşı çalışan testler (`examples/`). Bunlar ürünün *çıktısıdır*.
- **Platformun kendi testleri:** Platformun doğru çalıştığını doğrulayan otomatik testler (`tests/`). Bu bölüm bunları anlatır.

Test piramidi yaklaşımı [4] izlendi: çok sayıda hızlı birim testi, daha az sayıda yavaş ama gerçekçi entegrasyon testi ve en üstte kullanıcı gözünden birkaç uçtan uca (E2E) test.

```
              ┌─────────┐
              │   E2E   │   8 test · ~48 sn · gerçek sunucu + worker + Chromium
             ┌┴─────────┴┐
             │Entegrasyon│  16 test · ~45 sn · gerçek Chromium, yerel sayfalar
           ┌─┴───────────┴─┐
           │     Birim     │ 69 test · ~1 sn · tarayıcı yok
           └───────────────┘
```

| Katman | Ne sınanır | Araç | Dış bağımlılık |
|--------|-----------|------|----------------|
| **Birim** | DSL doğrulama kuralları, veritabanı/kuyruk mantığı, API uç noktaları, web sayfaları ve formlar, CLI çıkış kodları, yardımcı fonksiyonlar | pytest, FastAPI `TestClient` | Yok. Her test geçici bir SQLite dosyası kullanır. |
| **Entegrasyon** | Worker + motor + gerçek Chromium; demo sitesine karşı örnek testler; görsel karşılaştırma | pytest, Playwright | Yok. Test kendi yerel HTTP sunucusunu açar; internet gerekmez. |
| **E2E** | Kullanıcının web arayüzünde yaptıkları: test yazma, koşturma, raporu okuma, süzme, silme, görsel referansı güncelleme | pytest-playwright | Yok. Test oturumu sunucuyu ve worker'ı ayrı süreçler olarak, geçici klasör ve veritabanıyla başlatır. |

**İlkeler**
- **Testler birbirinden ve geliştiricinin verisinden bağımsız:** Her test kendi geçici veritabanını ve klasörünü kullanır; `data/platform.db`'ye dokunulmaz.
- **İnternet yok:** Hiçbir otomatik test dış siteye gitmez. saucedemo.com örnekleri elle demo içindir; CI'da koşmaz. Gerekçe: dış site yavaşlayınca testler sebepsiz kalıyordu (hata kaydı H-08).
- **Sabit bekleme yok:** Platformun kendi E2E testleri de `sleep` kullanmaz. Örneğin koşunun bitmesi, rapor sayfası kendini yeniledikçe `expect(...).to_have_text("Geçti")` ile beklenir. (Tek istisna: sunucunun açılmasını bekleyen hazırlık kodu.)
- **Gereksinime bağlılık:** Her kabul kriterinin onu doğrulayan testi vardır (bkz. 2.3 ve 2.5 izlenebilirlik matrisi).
- **Kendi kendini test etme (dogfooding):** `examples/platform/arayuz.yaml`, platformun web editörünü platformun kendi YAML diliyle test eder. E2E testi bu YAML'ı worker'a koşturur.

## 5.2 Birim testleri (69 test)

| Dosya | Test sayısı | Kapsam |
|-------|------------:|--------|
| `tests/unit/test_dsl.py` | 25 | Geçerli tanım, varsayılanlar, `failOnPageErrors` seçeneği, örnek dosyaların geçerliliği; 19 hata senaryosu (bilinmeyen adım, eksik/çift locator, `name`'in `role`'süz kullanımı, eksik `value`, bilinmeyen alan, virgül ipucu, YAML sözdizimi hatası ve satır numarası, eksik/geçersiz `baseUrl`, boş adım listesi, negatif timeout, eksik dosya…) |
| `tests/unit/test_db.py` | 9 | Kuyruğun ilk giren ilk çıkar (FIFO) çalışması, bir işin iki kez alınamaması, YAML kopyası, yarıda kalan koşuların `error` olması, silmede CASCADE, süzgeçler |
| `tests/unit/test_api.py` | 9 | CRUD uç noktaları, 422 + Türkçe hata listesi, 404, kuyruğa almada 202, dosya adreslerinin üretilmesi, süzgeçler |
| `tests/unit/test_web.py` | 17 | Sayfaların açılması, sayfa hataları tablosu (ve içindeki mesajların kaçışlanması), formlar ve 303 yönlendirmeleri, hatalı kayıtta metnin korunması, **XSS kaçışı**, otomatik yenileme, demo sitesinin iki sürümü, görsel referans güncellemede **path traversal koruması** |
| `tests/unit/test_cli.py` | 4 | Çıkış kodları 0/2, geçersiz dosya varken hiçbir testin koşmaması |
| `tests/unit/test_helpers.py` | 5 | URL birleştirme, Türkçe karakterli klasör adları, hata mesajı kısaltma, Command nesnelerinin üretilmesi |

## 5.3 Entegrasyon testleri (16 test)

| Dosya | Test sayısı | Kapsam |
|-------|------------:|--------|
| `tests/integration/test_worker.py` | 3 | Kuyruk → worker → Chromium → veritabanı: geçen test; kalan test (ekran görüntüsü + trace + atlanan adımlar); tarayıcı açılamazsa `error` |
| `tests/integration/test_demo_site.py` | 3 | Demo örnekleri Sürüm 1.0'da geçer; sipariş testi Sürüm 2.0'da tam olarak sepet toplamı adımında kalır (sunum senaryosunun korunması) |
| `tests/integration/test_page_errors.py` | 4 | Otomatik sayfa hatası yakalama (B1): Sürüm 1.0'da **sıfır** hata (gürültü filtresi), 2.0'daki üç bilinçli hatanın türüyle yakalanması, `failOnPageErrors` ile testin kalması ve trace'in saklanması, ulaşılamayan sunucu / tekrarlanan hata / favicon gürültüsü |
| `tests/integration/test_visual.py` | 6 | Görüntü karşılaştırma fonksiyonu (aynı görüntü, 100 piksellik değişiklik, küçük renk gürültüsü, farklı boyut); demo sitesinde referans oluşturma → aynı sürümde %0 fark → 2.0'da farkın yakalanması; referans güncelleme |

## 5.4 Uçtan uca (E2E) testleri (8 test)

`tests/e2e/test_platform_e2e.py`. Her test gerçek bir kullanıcı gibi web arayüzünü kullanır.

| # | Test | Kullanıcı hikâyesi | Ne doğrulanır |
|---|------|-------------------|---------------|
| E2E-1 | `test_create_test_in_editor` | US-1 | Editörde YAML yazılır, canlı doğrulama "✓ Geçerli · 8 adım" der, kaydedilir, listede görünür |
| E2E-2 | `test_invalid_test_is_rejected_with_turkish_errors` | US-1 | Hatalı adım yazarken "4. adım: bilinmeyen adım tipi 'tikla'" görünür; kaydetme reddedilir, yazılan kaybolmaz |
| E2E-3 | `test_passing_run_shows_passed_report` | US-2 | "Koştur" → rapor sayfası "Sırada"dan "Geçti"ye döner; 15 adım, ekran görüntüsü yüklü, sayfa hatası bölümü **yok** (1.0 temiz) |
| E2E-4 | `test_regression_in_v2_is_caught_with_evidence` | US-3 | Sürüm 2.0 regresyonu: "Kaldı", hata kutusunda "1.250 TL", 1 kalan + 5 atlanan adım, ekran görüntüsü gerçekten yüklenmiş, trace indirilebilir; ayrıca test sormadığı halde "Sayfa hataları (3)" bölümü (B1) |
| E2E-5 | `test_run_history_can_be_filtered_by_status` | US-4 | Koşular sayfasında "Kaldı" süzgeci yalnızca kalan koşuları gösterir |
| E2E-6 | `test_delete_test_asks_for_confirmation` | — | Silme onay penceresi; onaydan sonra test listeden kalkar |
| E2E-7 | `test_platform_tests_its_own_ui_with_its_own_dsl` | — | Platform, kendi editörünü kendi YAML diliyle test eder ve geçer |
| E2E-8 | `test_visual_regression_flow` | FR-14 | Referans oluştur → editörde testi 2.0'a yönlendir → görsel fark yakalanır, üç görüntü yüklü → "yeni referans yap" → tekrar koşu %0 farkla geçer |

## 5.5 Fonksiyonel test senaryoları (elle, sunum provası için)

Otomatik testlerin yanında, sunumda canlı gösterilecek akışlar elle de denendi. Hepsi otomatik bir testle de güvence altında.

| # | Senaryo | Adımlar | Beklenen sonuç | Otomatik karşılığı |
|---|---------|---------|----------------|-------------------|
| FS-1 | Hatalı test yazma | Yeni test → bir adımı `tikla` yap, bir adıma ikinci locator ekle | Yazarken iki hata adım numarasıyla görünür; kaydedilmez | E2E-2 |
| FS-2 | Yeni sürümde regresyon | "Demo - Sipariş akışı (Sürüm 1.0)" koştur, sonra "(Sürüm 2.0)" koştur | 1.0 geçer; 2.0 10. adımda kalır, "1.250 TL" ve ekran görüntüsü görünür | E2E-3, E2E-4 |
| FS-3 | Görsel regresyon | "Demo - Sepet görsel kontrol"ü koştur, adresini `/demo-v2` yap, tekrar koştur | İlk koşu referans oluşturur; ikinci koşu fark görüntüsüyle kalır | E2E-8 |
| FS-4 | Tüm testleri koştur | Testler → "Tümünü koştur" | Koşular sayfası kendini yeniler, sırayla sonuçlanır | E2E-5 (kısmen) |
| FS-5 | Platform hatası | Worker kapalıyken bir test koştur | Rapor "Sırada" kalır ve "worker çalışmıyor olabilir" ipucu görünür | `test_web::test_run_button_queues_and_redirects_to_report` |

## 5.6 Test sonuçları

Son tam koşu (27.11.2026, Windows 11, Python 3.12, Chromium 159 headless):

| Katman | Test | Geçti | Kaldı | Süre |
|--------|-----:|------:|------:|-----:|
| Birim | 69 | 69 | 0 | ~1 sn |
| Entegrasyon | 16 | 16 | 0 | ~45 sn |
| E2E | 8 | 8 | 0 | ~38 sn |
| **Toplam** | **93** | **93** | **0** | **~84 sn** |

- Her `python -m pytest` çalıştırması `reports/junit.xml` (makine okur) ve `reports/test-raporu.html` (tarayıcıda açılan tek dosyalık rapor) üretir. Teslimde HTML rapor eklere konacak.
- **Sürekli entegrasyon:** `.github/workflows/ci.yml` her push ve pull request'te aynı testleri temiz bir Ubuntu makinesinde koşturur, YAML örneklerini doğrular, katman katman özet tablo yazar ve raporları 14 gün saklar.

**İlk CI koşusu** (25.11.2026, o tarihte 86 test, [GitHub Actions #1](https://github.com/FurkanHaltas/ui-test-platform/actions/runs/45630609044), Ubuntu, `ubuntu-latest`): **başarılı**, toplam 2 dk 7 sn. Ekran görüntüsü: [11-ci-github-actions.png](ekran-goruntuleri/11-ci-github-actions.png).

| CI adımı | Süre |
|----------|-----:|
| Kodu al, Python 3.12 kur, bağımlılıkları kur | 17 sn |
| Chromium'u sistem kütüphaneleriyle kur | 33 sn |
| Örnek YAML'ları doğrula + geçersiz örneğin reddi | < 1 sn |
| **86 testi koştur** | **66 sn** |
| Test özetini yaz, raporları sakla | 1 sn |

Testlerin Windows'ta (geliştirme) ve Linux'ta (CI) aynı sonucu vermesi, platformdan bağımsızlık gereksinimini (NFR-08) de doğruluyor.

## 5.7 Tespit edilen ve giderilen hatalar

Ayrıntılı kayıt: [hata-kaydi.md](hata-kaydi.md) (belirti, kök neden, çözüm, doğrulama). Özet:

| No | Hata | Nasıl bulundu | Durum |
|----|------|---------------|-------|
| H-01 | Sepet testinde yanlış locator | Örnek test koşusu | ✅ |
| H-02 | İndirilen Chromium görünür modda açılmıyor | Elle deneme | ⚠️ `--channel chrome` |
| H-03 | Windows dosya yolları web adresini bozacaktı | Tasarım incelemesi | ✅ |
| H-04 | Türkçe buton bulunamadı (karakter kodlaması) | Entegrasyon testi | ✅ |
| H-05 | Konsolda ✓ karakteri programı çökertti | Seed betiği | ✅ |
| H-06 | Test istemcisi kullanımdan kaldırma uyarısı | Birim testi uyarısı | 🔓 |
| H-07 | Virgüllü değer "bilinmeyen alan" sanılıyordu | Örnek YAML doğrulaması | ✅ |
| H-08 | Yavaş dış sitede testler sayfa açılırken kaldı | Web arayüzünden canlı koşu | ✅ |
| H-09 | Editörde hata kutusu ekran dışında kalıyordu | Elle inceleme | ✅ |
| H-10 | Koşu süzgecinde "Tüm testler" seçiliyken sayfa yerine JSON hatası | **E2E testi** | ✅ |
| H-11 | E2E testleri entegrasyon testlerinden önce koşunca Playwright çakışması | Test sırası denemesi | ✅ |
| H-12 | CI'da kullanımdan kalkan Node.js 20 uyarısı | İlk CI koşusu | ✅ |
| H-13 | `failOnPageErrors` ile kalan testte trace kaydedilmiyordu | B1'in entegrasyon testi | ✅ |

Dikkat çekici olan: H-04 ve H-10 doğrudan platformun kendi otomatik testleri tarafından bulundu. H-07'yi ise platformun doğrulayıcısı, örnek test yazılırken yakaladı.
