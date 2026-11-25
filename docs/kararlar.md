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

---

# Tasarım Kararları (Aşama 2 — API, Veritabanı, Worker)

## K14. API testi kendisi koşturmaz; kuyruk + ayrı worker süreci
- **Ne:** `POST /api/tests/{id}/runs` sadece `runs` tablosuna `queued` bir satır ekler ve hemen **202 Accepted** döner. Testi ayrı bir süreç olan worker koşturur. İstemci sonucu `GET /api/runs/{id}` ile sorgular.
- **Neden:** Bir E2E testi saniyeler, hatta dakikalar sürebilir. API isteği bu süre boyunca açık kalırsa zaman aşımına uğrar ve sunucu kilitlenir. Ayrı süreç olunca tarayıcı çökse bile API ayakta kalır. İleride daha fazla worker ekleyerek ölçeklenebilir.
- **Alternatif:** FastAPI `BackgroundTasks`. Daha az parça, ama test API ile aynı süreçte çalışır; API yeniden başlarsa iş kaybolur, ölçeklenemez.

## K15. Kuyruk = veritabanı tablosu (ayrı kuyruk sistemi yok)
- **Ne:** `status = 'queued'` satırları kuyruktur. Worker işi tek bir SQL cümlesiyle alır:
  `UPDATE runs SET status='running' WHERE id = (en eski queued) AND status='queued' RETURNING *`
- **Neden:** Redis/RabbitMQ gibi ek bir servis kurmak gerekmez, durum zaten veritabanında. Tek cümle olduğu için **atomiktir**: iki worker aynı anda sorsa bile aynı işi ikisi birden alamaz.
- **Bedel:** Worker kuyruk boşken saniyede bir veritabanına bakar (*polling*). Bu ders projesi ölçeğinde önemsiz bir yük.
- **Not:** Bu bekleme, test adımlarındaki "sabit sleep yasağı" (K7) ile çelişmez. O kural, sayfanın hazır olmasını tahminle beklemeyi yasaklıyor; burada ise sadece boş kuyruğa ne sıklıkla bakılacağı belirleniyor.

## K16. SQLite + düz SQL (ORM yok)
- **Neden:** İki tablo için ORM (SQLAlchemy) öğrenme ve açıklama yükü getirir. Python'un yerleşik `sqlite3` modülüyle her sorgu açıkça görünür. SQLite tek dosyadır, kurulum gerektirmez.
- **WAL modu:** API ve worker aynı dosyaya aynı anda erişir. WAL (write-ahead log) modunda biri yazarken diğerleri okumaya devam edebilir. `timeout=10` sayesinde aynı anda iki yazma olursa biri hata vermek yerine bekler.
- **Bağlantı:** Her HTTP isteği kendi bağlantısını alır ve kapatır (FastAPI `Depends`). Paylaşılan bağlantının thread sorunları olmaz.
- **Konum:** `api/db.py`. Worker da bu modülü kullanır; ayrı bir paket açmak iki tüketici için gereksiz soyutlama olurdu.

## K17. Koşu, YAML'ın bir kopyasını saklar
- **Ne:** Kuyruğa alırken testin o anki YAML'ı `runs.yaml` sütununa kopyalanır.
- **Neden:** Kullanıcı testi koşu kuyruktayken ya da bittikten sonra düzenleyebilir. Raporun "hangi adımlar koşturuldu" sorusuna her zaman doğru cevap vermesi gerekir (izlenebilirlik).

## K18. Sonuç JSON olarak tek sütunda (`result_json`)
- **Ne:** Motorun `RunResult` çıktısı olduğu gibi saklanır. Sorgulanması gereken alanlar (durum, süre, hata) ayrı sütunlarda tutulur.
- **Neden:** Adım sonuçları her zaman bir koşuyla birlikte okunur, tek başına sorgulanmaz. Ayrı bir `run_steps` tablosu daha fazla kod getirir ama bir fayda sağlamaz. Motor ve API aynı modeli (K9) paylaşır.

## K19. `failed` ile `error` ayrımı
- **`failed`:** Test çalıştı, bir adım kaldı. Test, *sitede* bir sorun buldu.
- **`error`:** Test hiç çalışamadı (tarayıcı açılamadı, worker yarıda kapandı). Sorun *platformda*.
- **Neden:** Kullanıcının "sitem mi bozuk, test aracı mı?" sorusunu ayırt edebilmesi gerekir. Worker açılırken `running` durumunda kalmış koşuları `error` yapar (MVP'de tek worker varsayımı).

## K20. Doğrulama hatası 422 + Türkçe liste; ayrı `/api/validate`
- **Ne:** Geçersiz YAML kaydedilmez; yanıt `{"message": "Test tanımı geçersiz", "errors": [...]}` olur. `/api/validate` ise kaydetmeden kontrol eder.
- **Neden:** Hata mesajları motorla aynıdır, tek kaynak `dsl.py`'dir. Aşama 3'teki web editörü `/api/validate` ile yazarken canlı kontrol yapabilecek. Testin adı YAML'daki `name` alanından alınır; ayrı bir alan iki yerde tutarsızlık yaratırdı.

## K21. Dosyalar statik olarak sunulur
- **Ne:** `artifacts/` klasörü `/artifacts` adresine bağlanır (`StaticFiles`). Her koşunun dosyaları `artifacts/runs/<koşu no>/` altındadır. API yanıtında yollar `screenshot_url` ve `trace_url` adreslerine çevrilir.
- **Neden:** Web arayüzü ekran görüntüsünü doğrudan `<img src>` ile gösterebilir. Motor yolları `/` ile yazar (`as_posix`), böylece Windows'taki `\` karakterleri URL'yi bozmaz.

## K22. Testler üç katmanlı
- **Birim (DSL, DB, API):** Tarayıcı açmaz, bir saniyenin altında biter. Her test geçici bir veritabanı kullanır (`UITP_DB` ortam değişkeni).
- **Entegrasyon (worker):** Gerçek Chromium ile, internete bağımlı olmadan, testin kendi açtığı yerel HTML sayfasına karşı çalışır.
- **Platformun kendi E2E testleri:** Aşama 4'te.

---

# Tasarım Kararları (Aşama 3 — Web Arayüzü ve Demo Sitesi)

## K23. Sunucu tarafında üretilen sayfalar (Jinja2), SPA değil
- **Ne:** Sayfalar FastAPI içinde Jinja2 şablonlarıyla üretilir. Formlar klasik HTML formudur. JavaScript sadece editördeki canlı doğrulama için kullanılır (`web/static/editor.js`, ~70 satır).
- **Neden:** React/Vue gibi bir tek sayfa uygulaması (SPA) ikinci bir dil, derleme adımı (npm, bundler) ve ayrı bir proje getirirdi. Sunucu tarafı sayfalar tek dilde (Python) kalır, her satırı açıklanabilir ve JavaScript kapalıyken bile çalışır.
- **Bedel:** Koşu sürerken sayfa canlı güncellenmek yerine birkaç saniyede bir yenilenir (K26). Bu ölçekte kullanıcı farkı hissetmez.

## K24. Web sayfaları veritabanına doğrudan erişir, doğrulama motorda
- **Ne:** Web rotaları (`web/routes.py`) kendi JSON API'mize HTTP isteği atmaz; aynı `api/db.py` fonksiyonlarını çağırır. Doğrulama her yerde motorun `parse_test` fonksiyonuyla yapılır.
- **Neden:** Aynı süreç içinde kendine HTTP isteği atmak gereksiz bir katmandır. Kurallar ve Türkçe hata mesajları tek yerde (`engine/dsl.py`) olduğu için CLI, API ve web hep aynı cevabı verir.
- **Post/Redirect/Get:** Form gönderilince işlem yapılır ve `303` ile yeni sayfaya yönlendirilir. Kullanıcı sayfayı yenilediğinde test ikinci kez kaydedilmez veya kuyruğa alınmaz.
- **Güvenlik:** Kullanıcının yazdığı YAML sayfaya basılırken Jinja2 otomatik olarak kaçışlar (`<` → `&lt;`). Canlı doğrulamada mesajlar `textContent` ile eklenir. Bu sayede YAML'a yazılan `<script>` çalışmaz (XSS koruması, `test_web::test_user_text_is_escaped`).

## K25. Yerel demo sitesi, iki sürüm
- **Ne:** `demo_site/` klasöründe sunucusuz küçük bir mağaza (Mini Market) var. Aynı API sunucusu bunu iki adreste yayınlar: `/demo` (Sürüm 1.0, doğru) ve `/demo-v2` (Sürüm 2.0, sepet toplamı bilerek hatalı). Sürümü JavaScript adres çubuğundan anlar.
- **Neden:**
  - Hocanın şartı: uygulama sunumda canlı test edilecek. Sınıfta internet olmasa da, saucedemo.com o gün yavaş ya da değişmiş olsa da (bkz. H-08) demo çalışmalı.
  - İki sürüm, platformun asıl amacını gösteren bir hikâye kurar: "yeni sürüm yayına alınmadan test edildi, regresyon yakalandı."
- **Gerçekçilik:** Giriş 0,6 sn, ürün listesi 0,4 sn gecikmeyle gelir. Testler sabit bekleme olmadan, Playwright'ın otomatik beklemesiyle geçer; K7'deki kararın canlı kanıtı.
- **Test kimlikleri:** Demo sitesi Playwright'ın varsayılanı olan `data-testid` özniteliğini kullanır, örneklerde `testIdAttribute` gerekmez.

## K26. Koşu sırasında otomatik yenileme (`meta refresh`)
- **Ne:** Rapor sayfası koşu `queued`/`running` durumundayken 2 sn'de, koşu listesi 3 sn'de bir kendini yeniler. Koşu bitince yenileme durur.
- **Neden:** Tek satır HTML'dir, JavaScript gerektirmez. WebSocket veya Server-Sent Events gerçek zamanlı olurdu ama hem sunucuda hem istemcide ek kod ister.

## K27. `goto` sadece HTML'in hazır olmasını bekler
- **Ne:** `page.goto(..., wait_until="domcontentloaded")`.
- **Neden:** Varsayılan `load` olayı, resimler ve reklam/analitik betikleri gibi testi ilgilendirmeyen bütün kaynakları bekler. Yavaş bir sitede testi gereksiz yere kaldırıyordu (H-08). Sonraki adımlar öğeleri zaten kendileri beklediği için güvenilirlik kaybı olmaz.
