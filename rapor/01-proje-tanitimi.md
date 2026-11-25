# 1. Proje Tanıtımı

## 1.1 Projenin adı
**Otomatik UI Test Platformu.** Web uygulamalarının kullanıcı akışlarını, kod yazmadan tanımlanan testlerle gerçek bir tarayıcıda otomatik olarak sınayan platform.

## 1.2 Problem tanımı
Web uygulamaları sık güncellenir. Her güncellemeden sonra giriş yapma, ürün arama, sepete ekleme gibi temel akışların hâlâ çalıştığını kontrol etmek gerekir. Bu kontrol bugün iki yolla yapılıyor ve ikisinin de sorunu var:

1. **Elle test:** Bir kişi her sürümde aynı adımları tarayıcıda tek tek tekrarlar. Yavaştır, sıkıcıdır, insan hatasına açıktır. Bir şey kırıldığında neyin, hangi adımda kırıldığının kanıtı (ekran görüntüsü, sayfa durumu) genellikle kaydedilmez.
2. **Kodla yazılan otomatik testler** (Selenium, Playwright, Cypress): Güçlüdür ama programlama bilgisi gerektirir. Test uzmanları ve ürün ekipleri test yazmak için geliştiricilere bağımlı kalır. Ayrıca kötü yazılmış testler sabit beklemeler (`sleep`) yüzünden kimi zaman geçip kimi zaman kalır (*flaky test*) ve güven kaybettirir.

Kısacası, **programcı olmayan birinin güvenilir bir uçtan uca (E2E) test yazıp çalıştırabileceği ve sonucunu kanıtıyla görebileceği** basit bir araç eksik.

## 1.3 Projenin amacı
- Testlerin **YAML formatında, adım adım ve kod yazmadan** tanımlanabilmesi (`goto`, `fill`, `click`, `expectText`…).
- Hatalı bir test tanımının, **hangi adımda ne hata olduğunu söyleyen Türkçe mesajlarla** daha çalıştırılmadan reddedilmesi.
- Testlerin **gerçek bir tarayıcıda** (Chromium), birbirinden **izole** ve **sabit bekleme kullanılmadan** güvenilir biçimde koşturulması.
- Her koşunun adım adım **raporlanması**; kalan testlerde **ekran görüntüsü ve trace** (adım adım kayıt) ile hatanın kanıtlanması.
- Testlerin ve sonuçların **saklanması**, bir **API** ve **web arayüzü** üzerinden yönetilmesi; uzun süren koşuların **kuyruk + arka plan işleyici** ile kullanıcıyı bekletmeden yürütülmesi.

## 1.4 Hedef kullanıcılar
| Kullanıcı | İhtiyacı | Platformu nasıl kullanır |
|-----------|----------|--------------------------|
| **Test uzmanı / QA** | Programlama bilmeden regresyon testi yazmak | YAML ile test yazar, web arayüzünden koşturur, raporu inceler |
| **Yazılım geliştirici** | Kırılan akışı hızlıca bulmak; testleri CI'da çalıştırmak | Kalan testin ekran görüntüsüne ve trace'ine bakar; CLI'ı CI hattında kullanır |
| **Proje / ürün yöneticisi** | Sürümün yayına hazır olup olmadığını görmek | Testlerin son durumunu ve koşu geçmişini izler |
| **Diğer sistemler** | Testleri otomatik tetiklemek | REST API ile test kaydeder, koşu başlatır, sonucu sorgular |

## 1.5 Projenin kapsamı

### Kapsam içinde
- YAML tabanlı test tanım dili (DSL): 7 adım tipi (`goto`, `click`, `fill`, `expectVisible`, `expectText`, `expectUrl`, `screenshot`) ve 5 öğe bulma yöntemi (`role`+`name`, `label`, `testId`, `text`, `css`).
- Test tanımlarının doğrulanması ve Türkçe hata mesajları.
- Playwright ile Chromium'da test koşturma, adım ve test bazında zaman aşımı.
- Hata anında ekran görüntüsü ve trace kaydı, JSON sonuç raporu.
- Komut satırı arayüzü (CLI).
- REST API (FastAPI), SQLite veritabanı, veritabanı tabanlı iş kuyruğu ve worker.
- Web arayüzü: test listesi, YAML editörü, koşu geçmişi, rapor ekranı. *(Aşama 3)*
- Platformun kendi otomatik testleri ve GitHub Actions ile sürekli entegrasyon. *(Aşama 4)*

### Kapsam dışında
- Firefox ve WebKit (Safari) tarayıcıları: sadece Chromium tabanlı tarayıcılar.
- Kullanıcı hesabı, oturum açma ve yetkilendirme: platform tek kullanıcılı, yerel kullanım için tasarlandı.
- Testlerin paralel koşturulması, dağıtık worker'lar.
- Mobil uygulama testi, yük/performans testi, API testi.
- Değişkenler, döngüler, koşullu adımlar gibi programlama dili özellikleri (DSL bilinçli olarak basit tutuldu).

Bonus olarak, zaman kalırsa: görsel regresyon (ekran görüntüsü karşılaştırma), kaydedici (Playwright codegen çıktısını YAML'a çevirme), yapay zekâ ile hata açıklama, tekrar deneme / flaky işareti (bkz. ROADMAP.md).
