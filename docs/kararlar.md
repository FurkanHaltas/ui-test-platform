# Tasarım Kararları (Aşama 1 — Test Motoru)

Her karar için: **ne** seçildi, **neden**, **alternatif** neydi.

---

## K1. Testler kod yerine YAML ile tanımlanır
- **Ne:** Kullanıcı `steps:` listesine `goto`, `click`, `fill`… gibi adımlar yazar.
- **Neden:** Hedef kitle programcı olmayan test uzmanları olabilir. YAML okunur, sürüm kontrolüne (git) uygundur ve ileride web arayüzünden üretilebilir.
- **Alternatif:** Doğrudan Python/pytest testi yazmak. Daha esnek, ama kod bilgisi gerektirir ve "kod yazmadan test" fikrine aykırı.

## K2. DSL doğrulaması Pydantic v2 ile, adım adım
- **Ne:** Kök alanlar (`name`, `baseUrl`, `timeout`…) tek bir Pydantic modeliyle doğrulanır. Adımlar döngüyle tek tek doğrulanır: önce adım tipi bilinen bir tip mi, sonra içeriği o tipin modeline uyuyor mu.
- **Neden:** Pydantic tip kontrolünü, zorunlu alanları ve bilinmeyen alanları (`extra="forbid"`) bedavaya verir. Adımları tek tek doğrulamak, hata mesajında **"3. adım (fill): 'value' alanı zorunlu"** gibi kesin bir konum vermeyi sağlar.
- **Alternatif:** Tek bir büyük "discriminated union" modeli. Daha az kod, ama Pydantic'in ürettiği hata konumları (`steps.2.fill.value`) ve İngilizce mesajlar kullanıcı için anlaşılmaz.
- **Ek:** Pydantic'in İngilizce hata kayıtları `_translate_error` fonksiyonuyla Türkçeye çevrilir. Tüm adım hataları **birlikte** gösterilir; kullanıcı her düzeltmeden sonra yeniden çalıştırmak zorunda kalmaz.

## K3. Her adımda tam olarak bir locator
- **Ne:** `role`(+`name`), `label`, `testId`, `text`, `css` alanlarından **yalnızca biri** verilebilir. `name`, sadece `role` ile kullanılabilir.
- **Neden:** İki locator verilirse hangisinin geçerli olduğu belirsizleşir. Kuralı doğrulamada zorlamak, hatayı tarayıcı açılmadan, anında yakalar.
- **Öncelik sırası:** Playwright'ın önerisiyle aynı: kullanıcının gördüğüne en yakın olan (rol, etiket) en sağlamdır, CSS en kırılgandır (tasarım değişince bozulur).

## K4. Command (komut) tasarım deseni
- **Ne:** Her adım tipi ayrı bir sınıftır (`GotoStep`, `ClickStep`, `FillStep`…). Hepsinin ortak arayüzü `execute(page, timeout)` ve `describe()` metotlarıdır.
- **Neden:** Koşucu (runner) adımların ne yaptığını bilmek zorunda kalmaz, sadece sırayla `execute` çağırır. Yeni adım tipi eklemek koşucuyu değiştirmez (açık/kapalı ilkesi). Her sınıf küçüktür ve tek başına açıklanabilir.
- **Sapma:** Promptta `execute(page)` yazıyordu. `timeout` parametresini ekledik, çünkü adımın süresi çalışma anında hesaplanıyor: "adımın kendi süresi" ile "testin kalan süresi"nin küçüğü (bkz. K7). Bunu nesnenin içinde saklamak, nesneyi her koşuda değiştirmek demek olurdu.
- **Alternatif:** Tek bir büyük `if kind == "click": ...` fonksiyonu. Kısa, ama büyüdükçe okunmaz olur ve test edilmesi zorlaşır.

## K5. DSL modeli ile komut nesneleri ayrı
- **Ne:** `dsl.py` "ne yapılacağını" tarif eden veri nesneleri (`StepSpec`) üretir. `steps.py` bunları "nasıl yapılacağını" bilen komutlara çevirir (`build_steps`).
- **Neden:** DSL doğrulaması Playwright'a bağımlı değildir, bu yüzden birim testleri tarayıcı açmadan milisaniyeler içinde çalışır. İleride API de aynı doğrulamayı tarayıcısız kullanabilir.

## K6. Her test için yeni browser context
- **Ne:** Tarayıcı (browser) bütün koşu için bir kez açılır, her test kendi `browser.new_context()`'ini alır.
- **Neden:** Context, kendi çerezleri, localStorage'ı ve oturumu olan temiz bir "gizli pencere" gibidir. Testler birbirinin oturumundan etkilenmez (izolasyon). Context açmak, tarayıcı açmaktan çok daha ucuzdur.

## K7. Sabit sleep yok, iki seviyeli timeout
- **Ne:** `time.sleep` hiç kullanılmaz. Playwright'ın kendi bekleme mekanizmaları kullanılır:
  - `click`/`fill` öğe görünür ve tıklanabilir olana kadar bekler (**auto-wait**).
  - `expect(...)` koşul sağlanana kadar tekrar tekrar kontrol eder (**web-first assertion**).
- **Timeout:** `stepTimeout` (varsayılan 10 sn, adımda `timeout:` ile ezilebilir) ve `timeout` (testin tamamı, varsayılan 60 sn). Her adıma verilen süre = `min(adım süresi, testin kalan süresi)`.
- **Neden:** Sabit sleep ya gereksiz yavaşlatır ya da yetmez ve testi rastgele kırar (flaky test). Koşul bazlı bekleme hem hızlı hem güvenilirdir. Test seviyesindeki sınırı thread/sinyal kullanmadan, sadece kalan süreyi hesaplayarak uyguluyoruz. Basit ve Windows'ta da sorunsuz.

## K8. Hata anında dur, ekran görüntüsü al, trace sakla
- **Ne:** Bir adım kalınca kalan adımlar `skipped` olarak işaretlenir, `hata-adim-N.png` alınır ve `trace.zip` kaydedilir.
- **Neden:** E2E adımları birbirine bağlıdır. Giriş başarısızsa sepete ekleme adımını denemenin anlamı yoktur. Ekran görüntüsü "ne oldu"yu, trace (Playwright'ın her adımın DOM'unu, ağ isteklerini ve ekranını kaydettiği dosya) "neden oldu"yu gösterir.
- **Trace sadece kalan testlerde:** Geçen testlerin trace'i kimsenin bakmayacağı disk yüküdür (Playwright'taki `retain-on-failure` yaklaşımı).

## K9. Sonuç modeli Pydantic + JSON dosyası
- **Ne:** `RunResult` → `StepResult` listesi (durum, süre, hata, ekran görüntüsü yolu). Her koşu `artifacts/<tarih-saat>_<test-adı>/result.json` dosyasına yazılır.
- **Neden:** Aşama 2'de API ve veritabanı aynı modeli kullanacak; JSON hem insan hem makine için okunur. Pydantic, JSON'a yazmayı ve geri okumayı tek satıra indirir.
- **Hata mesajı kısaltma:** Playwright hataları uzun bir "Call log" içerir. Raporda sadece özet tutulur; ayrıntı zaten trace'tedir.

## K10. Senkron Playwright API'si
- **Neden:** `async/await` gerektirmez, kod yukarıdan aşağıya okunur, savunmada anlatması kolaydır. Testler zaten sırayla koşuyor, eşzamanlılığın burada bir faydası yok. Paralel koşu gerekirse Aşama 2'de birden fazla worker *process* ile çözülecek.

## K11. `testIdAttribute` alanı
- **Ne:** `testId` locator'ının hangi HTML özniteliğine bakacağı test dosyasında seçilebilir (varsayılan `data-testid`).
- **Neden:** Siteler farklı öznitelik kullanır. Örneğin saucedemo.com `data-test` kullanır. Varsayılanı Playwright ile aynı tuttuk, örneklerde `testIdAttribute: data-test` yazıyoruz.

## K12. CLI çıkış kodları ve `--channel`
- **Çıkış kodları:** `0` hepsi geçti, `1` en az bir test kaldı, `2` geçersiz YAML veya tarayıcı açılamadı. Aşama 4'te GitHub Actions bu kodlara bakarak işi kırmızı/yeşil gösterecek.
- **Geçersiz dosya varsa hiçbir test koşmaz:** Kullanıcı yarım bir koşu sonucuyla yanılmasın.
- **`--channel chrome|msedge`:** Playwright'ın indirdiği Chromium yerine bilgisayardaki Chrome/Edge kullanılır (aynı Chromium motoru). Geliştirme makinesinde indirilen Chromium 159'un görünür (`--headed`) modu Windows'ta "side-by-side yapılandırma" hatası verdiği için eklendi. Headless mod indirilen Chromium ile sorunsuz çalışıyor.

## K13. Bilinçli olarak yapılmayanlar (şimdilik)
- Tekrar deneme (retry), paralel koşu, değişkenler, Firefox/WebKit: Kapsamı küçük ve açıklanabilir tutmak için. Bonus listesinde (ROADMAP.md).
- `placeholder` locator'ı yok: Promptta tanımlı 5 locator ile sınırlı kaldık.
