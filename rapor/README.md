# Proje Raporu — Çalışma Klasörü

Bu klasör, teslim edilecek **proje dokümanının** (12–20 sayfa) ve **sunumun** ham maddesidir. Bölümler Markdown olarak burada yazılır, teslimden önce tek bir Word/PDF belgesinde birleştirilir.

- Kod ve teknik tasarım belgeleri `docs/` altında kalır (`kararlar.md`, `uml/`). Bu klasör onlara bağlantı verir, içeriği kopyalamaz.
- **Sürekli güncellenen iki dosya:** [hata-kaydi.md](hata-kaydi.md) (her yeni hata) ve [kaynakca.md](kaynakca.md) (her yeni kaynak).

## Hocanın şablonuna göre durum

Durum: ✅ yazıldı · 🟡 malzeme hazır, rapor diline çevrilecek · ⏳ ilgili aşamada · ⬜ henüz yok

### 1. Çalışan yazılım uygulaması
| Kriter | Durum | Nerede |
|--------|-------|--------|
| Temel işlevler çalışıyor | ✅ | Motor, API, worker; web arayüzü ⏳ Aşama 3 |
| Veri saklama | ✅ | SQLite (`data/platform.db`), JSON sonuçlar, `artifacts/` |
| Arayüz (web/CLI/API) | ✅ | CLI + REST API; web ⏳ Aşama 3 |
| En az 3 fonksiyonel gereksinim | ✅ | 11 gereksinim gerçekleşti → [02-gereksinim-analizi.md](02-gereksinim-analizi.md) |
| En az bir hata/istisna yönetimi | ✅ | Türkçe doğrulama hataları, 404/422, timeout, `failed`/`error` ayrımı |
| Otomatik testler | ✅ | 53 test (`python -m pytest`) |
| Sürüm kontrolü | 🟡 | Yerel git var; **GitHub'a yüklenecek** (Aşama 4) |
| Kurulum/çalıştırma belgesi | ✅ | [../README.md](../README.md) |

### 2. Proje dokümanı
| Bölüm | Alt başlık | Durum | Kaynak |
|-------|-----------|-------|--------|
| **1. Proje tanıtımı** | Ad, problem, amaç, hedef kullanıcılar, kapsam | ✅ | [01-proje-tanitimi.md](01-proje-tanitimi.md) |
| **2. Gereksinim analizi** | Fonksiyonel / fonksiyonel olmayan gereksinimler | ✅ | [02-gereksinim-analizi.md](02-gereksinim-analizi.md) |
| | ≥3 kullanıcı hikâyesi + kabul kriterleri | ✅ | aynı dosya (6 hikâye, testlere bağlı) |
| | MoSCoW önceliklendirme | ✅ | aynı dosya |
| **3. Yazılım tasarımı** | Mimari | 🟡 | [bileşen diyagramı](../docs/uml/bilesen-diyagrami.md), README'deki şema |
| | Teknolojiler ve seçim gerekçeleri | 🟡 | [kararlar.md](../docs/kararlar.md) (K10, K14–K16 vb.) |
| | UML use case | ✅ | [use-case-diyagrami.md](../docs/uml/use-case-diyagrami.md) |
| | UML sınıf / bileşen | ✅ | [sinif-diyagrami.md](../docs/uml/sinif-diyagrami.md), [bilesen-diyagrami.md](../docs/uml/bilesen-diyagrami.md) |
| | Sequence | ✅ | [motor](../docs/uml/sequence-test-kosturma.md), [API üzerinden](../docs/uml/sequence-api-kosu.md) |
| | Veritabanı / veri modeli | ✅ | [er-diyagrami.md](../docs/uml/er-diyagrami.md) + DSL formatı (README) |
| **4. Uygulama geliştirme** | Geliştirme ortamı, klasör yapısı | 🟡 | README, CLAUDE.md |
| | Temel algoritmalar | 🟡 | kararlar K2 (doğrulama), K7 (timeout hesabı), K15 (atomik kuyruk) |
| | API / modül yapısı | 🟡 | README uç nokta tablosu, `/docs` (Swagger) |
| | Önemli kod bölümleri | ⬜ | Aşama 5'te seçilecek: `claim_next_run`, `_run_step`, `build_locator`, `_parse_step` |
| | Ekran görüntüleri | ⏳ | Aşama 3 (web arayüzü), Swagger, CLI çıktısı |
| **5. Yazılım testleri** | Test stratejisi | 🟡 | kararlar K22 |
| | Birim / entegrasyon testleri | ✅ | `tests/unit`, `tests/integration` |
| | Fonksiyonel test senaryoları | 🟡 | Kabul kriterleri + `examples/*.yaml`; E2E ⏳ Aşama 4 |
| | Test sonuçları | ⬜ | Aşama 4: pytest raporu (JUnit/HTML) + CI ekran görüntüsü |
| | Tespit edilen ve giderilen hatalar | ✅ | [hata-kaydi.md](hata-kaydi.md) |
| **6. Sonuç ve değerlendirme** | Gerçekleşen gereksinimler, sorunlar, çözümler, sınırlılıklar, iyileştirmeler | 🟡 | Gereksinim tablosu, hata kaydı, kapsam dışı listesi, ROADMAP bonusları |
| **7. Kaynakça** | | ✅ | [kaynakca.md](kaynakca.md) (sürekli güncellenir) |

### 3. Sunum (10–15 dk, uygulama canlı test edilecek)
| Konu | Durum |
|------|-------|
| İnternetten bağımsız yerel demo sitesi | ⏳ Aşama 3 sonu (saucedemo erişilemezse demo çökmesin) |
| Demo senaryosu (geçen + bilerek kalan test, hatalı YAML) | 🟡 `examples/` hazır |
| Görünür tarayıcı: `--channel chrome` | ⚠️ bkz. [H-02](hata-kaydi.md) |
| Slaytlar | ⏳ Aşama 5 |
