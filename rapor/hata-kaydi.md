# Tespit Edilen ve Giderilen Hatalar (Hata Kaydı)

Rapordaki "5. Yazılım Testleri → Tespit edilen ve giderilen hatalar" ile "6. Sonuç → Karşılaşılan sorunlar / Çözüm yaklaşımları" bölümlerinin kaynağıdır. **Her yeni hata bulunduğunda buraya eklenir.**

Durum: ✅ giderildi · ⚠️ geçici çözümle aşıldı · 🔓 açık

| No | Tarih | Aşama | Nasıl bulundu | Durum |
|----|-------|-------|---------------|-------|
| H-01 | 25.11.2026 | 1 | Örnek test koşusu | ✅ |
| H-02 | 25.11.2026 | 1 | `--headed` elle denemesi | ⚠️ |
| H-03 | 25.11.2026 | 2 | Tasarım incelemesi | ✅ |
| H-04 | 25.11.2026 | 2 | Entegrasyon testi | ✅ |
| H-05 | 25.11.2026 | 2 | Seed betiğinin çalıştırılması | ✅ |
| H-06 | 25.11.2026 | 2 | Birim testi uyarısı | 🔓 |
| H-07 | 25.11.2026 | 3 | Örnek YAML doğrulaması | ✅ |
| H-08 | 25.11.2026 | 3 | Web arayüzünden canlı koşu | ✅ |
| H-09 | 25.11.2026 | 3 | Rapor sayfasının elle incelenmesi | ✅ |

---

## H-01 — Sepet testinde ürün adı bulunamadı
- **Belirti:** `examples/sepete-ekle.yaml` 11. adımda 8 sn bekleyip kaldı: `expectVisible role=link[name="Sauce Labs Backpack"]` → *element(s) not found*. Ekran görüntüsünde ürün sepette açıkça görünüyordu.
- **Kök neden:** Test yanlış yazılmıştı. Sepet sayfasında ürün adı, erişilebilirlik ağacında `link` rolüyle o isimde bir öğe olarak yer almıyor. Locator, kullanıcının gördüğü ile tarayıcının gördüğü rolü karıştırmıştı.
- **Çözüm:** Adım `expectText: { testId: inventory-item-name, value: Sauce Labs Backpack }` olarak değiştirildi. Bu, ürünün sadece görünmesini değil, **doğru ürün** olduğunu da doğruluyor.
- **Ders:** Platformun kendi hata raporu (ekran görüntüsü + adım numarası) sorunun sitede değil testte olduğunu birkaç saniyede gösterdi. Bu, FR-05'in pratikteki faydasına iyi bir örnek.

## H-02 — Görünür modda (`--headed`) tarayıcı açılmıyor
- **Belirti:** `python -m engine run ... --headed` → `BrowserType.launch: spawn UNKNOWN`. Görünmez (headless) mod sorunsuz.
- **Kök neden:** Playwright'ın indirdiği Chromium 159 (`chrome.exe`) Windows tarafından başlatılmıyor. Olay günlüğünde *"yan yana (side-by-side) yapılandırması hatalı, bağımlı derleme bulunamadı"* hatası var. Headless mod ayrı bir program (`headless_shell`) kullandığı için etkilenmiyor. `playwright install --force chromium` ile yeniden kurmak sorunu çözmedi.
- **Çözüm (geçici):** CLI ve worker'a `--channel chrome|msedge` seçeneği eklendi. Bu, bilgisayarda kurulu Google Chrome'u (aynı Chromium motoru) kullanıyor; görünür mod bu şekilde çalışıyor.
- **Etkisi:** Sunumda görünür demo için `--channel chrome` kullanılmalı. CI (Linux) headless çalışacağı için etkilenmez.
- **Ayrıca:** Tarayıcı açılamadığında kullanıcı uzun bir yığın izi (stack trace) yerine Türkçe bir mesaj ve çözüm önerisi görüyor (çıkış kodu 2).

## H-03 — Windows dosya yolları web adresini bozacaktı
- **Belirti:** Motor dosya yollarını `artifacts\20261125-...\hata-adim-5.png` biçiminde (ters bölü ile) kaydediyordu.
- **Kök neden:** `str(Path)` Windows'ta `\` kullanır. API bu yolları `/artifacts/...` web adreslerine çevireceği için ters bölüler URL'yi bozacaktı.
- **Çözüm:** Motor yolları her işletim sisteminde `/` ile yazıyor (`Path.as_posix()`). API ayrıca `\` karakterlerini `/`'ye çeviriyor.
- **Doğrulama:** `test_api::test_run_detail_has_result_and_artifact_urls`; canlı denemede ekran görüntüsü adresi `200 image/png` döndü.

## H-04 — Entegrasyon testinde Türkçe buton bulunamadı
- **Belirti:** Worker testi 3. adımda kaldı: `click role=button[name="Gönder"]` → zaman aşımı.
- **Kök neden:** Testin kullandığı yerel HTML sayfasında `<meta charset="utf-8">` yoktu. Tarayıcı sayfayı başka bir karakter kodlamasıyla okudu, "Gönder" yazısı bozuk karakterlere dönüştü ve locator eşleşmedi.
- **Çözüm:** Test sayfasına `<meta charset="utf-8">` eklendi.
- **Ders:** Gerçek sitelerde de karşılaşılabilecek bir sorun. Türkçe karakter içeren locator'lar sayfanın karakter kodlamasına bağlıdır.

## H-05 — Konsol çıktısında ✓ karakteri programı çökertti
- **Belirti:** `python -m api.seed` çıktısı yönlendirildiğinde `UnicodeEncodeError: 'charmap' codec can't encode character '✓'`.
- **Kök neden:** Çıktı bir dosyaya ya da başka bir programa yönlendirildiğinde Windows eski Türkçe kod sayfasını (cp1254) kullanıyor; bu kod sayfasında ✓ ✗ → karakterleri yok. CLI'da bu durum baştan ele alınmıştı ama worker ve seed betiğinde unutulmuştu.
- **Çözüm:** Ortak bir yardımcı fonksiyon yazıldı (`engine/console.py → use_utf8_output`). CLI, worker ve seed betiği bunu kullanıyor (tekrar eden kod da böylece kalktı).

## H-06 — Test istemcisi kullanımdan kaldırma uyarısı
- **Belirti:** API testleri çalışırken Starlette uyarısı: test istemcisinin `httpx` ile kullanımı kullanımdan kaldırılıyor, `httpx2` öneriliyor.
- **Durum:** Testler doğru çalışıyor; uyarı `pytest.ini` içinde gizlendi. Paket değişikliği, önerilen paket doğrulanmadan yapılmadı (tedarik zinciri güvenliği: bilinmeyen paket kurmamak).
- **Yapılacak:** Aşama 4'te bağımlılıklar gözden geçirilirken ele alınacak.

## H-07 — Virgüllü değer "bilinmeyen alan" hatası veriyordu
- **Belirti:** `- fill: { label: Adres, value: Atatürk Cad. No 1, Ankara }` satırı "12. adım (fill): bilinmeyen alan 'Ankara'" hatası verdi.
- **Kök neden:** YAML'ın süslü parantezli yazımında virgül alan ayırıcıdır. `Ankara` değeri olmayan yeni bir alan sanıldı. Hata mesajı doğruydu ama kullanıcıya ne yapacağını söylemiyordu. Bu hatayı ilk kez platformun kendi doğrulayıcısı, örnek test yazılırken yakaladı.
- **Çözüm:** Değer tırnak içine alındı. Ayrıca doğrulayıcı, değeri boş olan bilinmeyen bir alan gördüğünde ipucu veriyor: *"değerde virgül varsa değeri tırnak içine alın, ör. value: "a, b""*. Editörün kısa rehberine de bu not eklendi.
- **Doğrulama:** `test_dsl::test_unquoted_comma_gives_hint`.

## H-08 — Yavaş dış sitede testler daha sayfa açılırken kaldı
- **Belirti:** Web arayüzünden "Tümünü koştur" yapıldığında saucedemo.com testlerinin üçü 1. adımda kaldı: `goto: zaman aşımı`. "Bilerek kalan test" de planlanan 5. adım yerine 1. adımda kaldı. Aynı anda yerel demo sitesinin testleri sorunsuz geçti.
- **Kök neden:** İki sorun üst üste geldi:
  1. `page.goto` varsayılan olarak sayfanın **tüm** kaynaklarının (resimler, dış betikler) yüklenmesini, yani `load` olayını bekliyordu. saucedemo o gün yavaştı (ana sayfa 4,1 sn), bu yüzden 10 sn'lik adım süresi aşıldı.
  2. `bilerek-kalan.yaml` hatayı çabuk göstermek için `stepTimeout: 3000` kullanıyordu. Bu kısa süre, kalması gereken adıma değil bütün adımlara, sayfa açılışına da uygulanıyordu.
- **Çözüm:**
  1. `goto` artık sadece HTML'in hazır olmasını (`domcontentloaded`) bekliyor. Sonraki adımlar zaten öğeleri kendileri beklediği için (auto-wait) güvenilirlik azalmadı.
  2. Örnekte kısa süre sadece kalması gereken adıma verildi: `expectText: { ..., timeout: 3000 }`.
- **Doğrulama:** Aynı gün yeniden koşuldu. saucedemo testleri 1,3–2,7 sn'de geçti, bilerek kalan test 5. adımda kaldı.
- **Ders:** Dış bir siteye bağlı testler, testi yazanın kontrolü dışındaki nedenlerle kalabilir (ağ, sitenin yükü). Sunum demosunun internetten bağımsız yerel demo sitesiyle yapılması kararının (K25) somut gerekçesi budur.

## H-09 — Uzun editörde hata kutusu ekranın dışında kalıyordu
- **Belirti:** Canlı doğrulama hataları editörün altında gösteriliyordu ama editör 22 satır yüksekliğinde olduğu için hata kutusu ilk ekranda görünmüyordu.
- **Çözüm:** Editör 15 satıra indirildi (gerekirse kullanıcı büyütebilir). Kod parçalarının satır sonunda bölünmesi de düzeltildi.
- **Doğrulama:** `rapor/ekran-goruntuleri/03-editor-canli-dogrulama.png`.
