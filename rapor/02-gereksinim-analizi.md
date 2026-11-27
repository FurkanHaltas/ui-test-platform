# 2. Gereksinim Analizi

Durum işaretleri: ✅ gerçekleştirildi · ⏳ planlandı (aşama numarasıyla) · ➖ kapsam dışı

## 2.1 Fonksiyonel gereksinimler

| No | Gereksinim | Öncelik | Durum |
|----|-----------|---------|-------|
| FR-01 | Kullanıcı bir testi YAML formatında, adım adım tanımlayabilmeli (7 adım tipi, 5 locator türü). | Must | ✅ |
| FR-02 | Sistem test tanımını çalıştırmadan önce doğrulamalı; hatalı tanımda hangi adımda ne hata olduğunu Türkçe bildirmeli ve tanımı kabul etmemeli. | Must | ✅ |
| FR-03 | Sistem testi gerçek bir Chromium tarayıcısında, her test için ayrı (izole) bir oturumla koşturmalı. | Must | ✅ |
| FR-04 | Her adım ve her test için zaman aşımı olmalı; süre dolunca adım başarısız sayılmalı. | Must | ✅ |
| FR-05 | Bir adım başarısız olunca test durmalı; o anın ekran görüntüsü ve trace kaydı alınmalı, kalan adımlar "atlandı" olarak işaretlenmeli. | Must | ✅ |
| FR-06 | Her koşu için adım bazında durum, süre ve hata mesajı içeren bir sonuç raporu üretilmeli ve saklanmalı. | Must | ✅ |
| FR-07 | Kullanıcı testleri kaydedebilmeli, listeleyebilmeli, düzenleyebilmeli ve silebilmeli. | Must | ✅ (API + web) |
| FR-08 | Kullanıcı kayıtlı bir testin koşturulmasını isteyebilmeli; istek beklemeden kabul edilmeli, koşu arka planda sırayla yapılmalı. | Must | ✅ |
| FR-09 | Kullanıcı bir koşunun sonucunu, adımlarını, ekran görüntülerini ve trace dosyasını görüntüleyebilmeli. | Must | ✅ (API + web) |
| FR-10 | Kullanıcı koşu geçmişini görebilmeli, teste ve duruma göre süzebilmeli; her testin son durumu listede görünmeli. | Should | ✅ |
| FR-11 | Testler komut satırından tek dosya ya da klasör olarak koşturulabilmeli; sonuç çıkış koduyla bildirilmeli (CI için). | Should | ✅ |
| FR-12 | Web arayüzü: test listesi, canlı doğrulamalı YAML editörü, koşu başlatma, koşu geçmişi ve rapor ekranı. | Must | ✅ |
| FR-13 | Platformun kendi testleri GitHub Actions'ta her değişiklikte otomatik koşmalı. | Should | ✅ |
| FR-14 | Görsel regresyon: ekran görüntüsünü önceki koşuyla karşılaştırma. | Could | ✅ (bonus) |
| FR-15 | Kaydedici: tarayıcıda yapılan işlemleri YAML teste çevirme. | Could | ⏳ Bonus |
| FR-16 | Yapay zekâ ile kalan testin hatasını açıklama. | Could | ⏳ Bonus |
| FR-17 | Tekrar deneme / flaky işareti, zamanlanmış testler, veri odaklı testler, bildirim. | Could | ⏳ Bonus |
| FR-18 | Firefox/WebKit desteği, kullanıcı hesapları, paralel koşu. | Won't | ➖ |
| FR-20 | Kullanıcı, kalan bir testin belirli sayıda yeniden denenmesini isteyebilmeli; önce kalıp sonra geçen test "kararsız" olarak işaretlenmeli ve önceki denemelerin kanıtları saklanmalı. | Could | ✅ (bonus B2) |
| FR-19 | Sistem, test yazılmasa da sayfadaki JavaScript hatalarını ve başarısız ağ isteklerini kaydedip raporlamalı; kullanıcı isterse bu durumda test kalmalı. | Could | ✅ (bonus B1) |

## 2.2 Fonksiyonel olmayan gereksinimler

| No | Kategori | Gereksinim | Nasıl sağlanıyor / ölçülüyor |
|----|----------|-----------|------------------------------|
| NFR-01 | Güvenilirlik | Testler sabit bekleme (`sleep`) kullanmamalı, sayfa hazır olduğunda ilerlemeli. | Playwright auto-wait ve `expect` (web-first assertion). Kodda test adımlarında `sleep` yok (kararlar K7). |
| NFR-02 | İzolasyon | Bir testin çerezi/oturumu diğerini etkilememeli. | Her test yeni `browser context` (K6). |
| NFR-03 | Kullanılabilirlik | Test yazmak programlama bilgisi gerektirmemeli; hata mesajları Türkçe ve konumlu olmalı. | YAML DSL; mesajlar "3. adım (fill): 'value' alanı zorunlu" biçiminde (K2). |
| NFR-04 | Performans | Doğrulama tarayıcı açmadan, 1 saniyenin altında yapılmalı. Koşturma isteği tarayıcıyı beklemeden yanıtlanmalı. | Tarayıcı açmayan 63 birim testi ~2 sn'de koşuyor. Koşu isteği 202 ile anında dönüyor (K14). |
| NFR-05 | Sağlamlık | Tarayıcı açılamaması, worker'ın yarıda kapanması gibi platform hataları test hatasından ayrı raporlanmalı; API çökmemeli. | `failed` / `error` ayrımı, yarıda kalan koşuların işaretlenmesi (K19). |
| NFR-06 | İzlenebilirlik | Bir koşunun hangi test tanımıyla yapıldığı sonradan değişmemeli. | Koşu, YAML'ın kopyasını saklar (K17). |
| NFR-07 | Sürdürülebilirlik | Yeni adım tipi eklemek koşucuyu değiştirmemeli; kod savunmada satır satır açıklanabilir olmalı. | Command pattern (K4), ORM'siz düz SQL (K16), Türkçe yorumlar. |
| NFR-08 | Taşınabilirlik ve kurulum | Python 3.11+ olan her makinede birkaç komutla kurulmalı; ek veritabanı sunucusu gerektirmemeli. | SQLite tek dosya; README'de 4 komutluk kurulum. Windows'ta geliştirildi, yollar platformdan bağımsız (`as_posix`). |
| NFR-09 | Test edilebilirlik | Kodun önemli kısımları otomatik testlerle doğrulanmalı. | 102 test: 73 birim, 21 entegrasyon, 8 E2E (bkz. 5. bölüm). |

## 2.3 Kullanıcı hikâyeleri ve kabul kriterleri

Kabul kriterleri *Verilen – Olduğunda – O zaman* (Given–When–Then) kalıbıyla yazıldı. Her kriterin yanında onu doğrulayan otomatik test belirtildi.

### US-1 — Kod yazmadan test tanımlama
> **Bir test uzmanı olarak**, bir giriş akışını kod yazmadan, adım adım YAML ile tanımlamak istiyorum, **böylece** test yazmak için bir geliştiriciye bağımlı kalmam.

| # | Kabul kriteri | Doğrulayan test |
|---|---------------|-----------------|
| AC-1.1 | **Verilen** geçerli bir YAML, **olduğunda** kaydedilince, **o zaman** test YAML'daki `name` ile listede görünür. | `test_api::test_create_test_takes_name_from_yaml`, `test_dsl::test_valid_test_is_parsed` |
| AC-1.2 | **Verilen** bilinmeyen bir adım tipi (`tikla`), **olduğunda** kaydedilmek istenince, **o zaman** "2. adım: bilinmeyen adım tipi 'tikla'" mesajı döner ve test kaydedilmez. | `test_api::test_invalid_yaml_returns_422_with_turkish_errors`, `test_dsl::test_unknown_step_type` |
| AC-1.3 | **Verilen** bir adımda hiç locator ya da birden fazla locator, **o zaman** hangi adım olduğu ve sorunun ne olduğu söylenir. | `test_dsl::test_missing_locator`, `test_dsl::test_two_locators_at_once` |
| AC-1.4 | **Verilen** birden fazla hatalı adım, **o zaman** tüm hatalar tek seferde listelenir. | `test_dsl::test_all_step_errors_are_reported_together` |
| AC-1.5 | **Olduğunda** kullanıcı web editöründe yazarken, **o zaman** hatalar kaydetmeden, yazmayı bırakınca gösterilir; hatalı kayıtta yazdıkları kaybolmaz. | `test_web::test_invalid_test_shows_errors_and_keeps_text`; canlı doğrulama elle doğrulandı (ekran görüntüsü 03) |

### US-2 — Testi arka planda koşturma
> **Bir test uzmanı olarak**, kayıtlı bir testi koşturmak ve sonucu beklerken başka işe devam edebilmek istiyorum, **böylece** uzun testler beni bekletmez.

| # | Kabul kriteri | Doğrulayan test |
|---|---------------|-----------------|
| AC-2.1 | **Olduğunda** koşu istenince, **o zaman** istek hemen `202` ve `queued` durumuyla yanıtlanır. | `test_api::test_queue_run_returns_202_and_queued` |
| AC-2.2 | **Verilen** kuyrukta birden fazla koşu, **o zaman** ilk gelen ilk koşturulur ve bir koşu iki kez alınmaz. | `test_db::test_queue_is_first_in_first_out`, `test_db::test_claimed_run_is_running_and_not_claimed_twice` |
| AC-2.3 | **Verilen** geçerli bir test, **olduğunda** worker koşturunca, **o zaman** durum `passed` olur ve her adım "geçti" olarak kaydedilir. | `test_worker::test_worker_runs_passing_test` |
| AC-2.4 | **Verilen** kuyruktaki bir koşu, **olduğunda** test sonradan düzenlenince, **o zaman** koşu eski (kuyruğa alındığı andaki) tanımla yapılır. | `test_db::test_run_keeps_yaml_snapshot` |

### US-3 — Kalan testin kanıtını görme
> **Bir geliştirici olarak**, bir test kaldığında hangi adımda ve neden kaldığını kanıtıyla görmek istiyorum, **böylece** hatayı tekrar üretmeye uğraşmadan düzeltebilirim.

| # | Kabul kriteri | Doğrulayan test |
|---|---------------|-----------------|
| AC-3.1 | **Verilen** 2. adımı kalan bir test, **o zaman** koşu `failed` olur ve hata "2. adım (expectVisible): …" ile başlar. | `test_worker::test_worker_records_failure_with_screenshot_and_trace` |
| AC-3.2 | **O zaman** kalan adımın ekran görüntüsü ve trace dosyası diske kaydedilir; sonraki adımlar `skipped` olur. | aynı test |
| AC-3.3 | **O zaman** API, ekran görüntüsü ve trace için tarayıcıda açılabilir adresler (`/artifacts/...`) verir. | `test_api::test_run_detail_has_result_and_artifact_urls` |
| AC-3.4 | **Verilen** geçen bir test, **o zaman** trace saklanmaz (disk tasarrufu). | `test_worker::test_worker_runs_passing_test` |
| AC-3.5 | **O zaman** web rapor sayfası kalan adımı kırmızıyla, ekran görüntüsünü sayfa içinde ve trace indirme bağlantısını gösterir. | `test_web::test_finished_report_shows_steps_screenshot_and_trace` |

### US-4 — Koşu geçmişini izleme
> **Bir proje yöneticisi olarak**, testlerin son durumunu ve geçmiş koşularını görmek istiyorum, **böylece** sürümün yayına hazır olup olmadığına karar verebilirim.

| # | Kabul kriteri | Doğrulayan test |
|---|---------------|-----------------|
| AC-4.1 | **O zaman** test listesinde her testin son koşusunun durumu görünür. | `test_db::test_last_run_status_on_test`, `test_api::test_queue_run_returns_202_and_queued` |
| AC-4.2 | **O zaman** koşular teste ve duruma göre süzülebilir; geçersiz durum değeri reddedilir. | `test_api::test_list_runs_filters`, `test_db::test_list_runs_filters` |
| AC-4.3 | **Verilen** test çalışamadıysa (tarayıcı açılamadı), **o zaman** durum `failed` değil `error` olur. | `test_worker::test_worker_marks_error_when_browser_cannot_start`, `test_db::test_stale_running_runs_become_error` |

### US-5 — Komut satırından / CI'da koşturma
> **Bir geliştirici olarak**, testleri komut satırından ve CI hattında çalıştırmak istiyorum, **böylece** her kod değişikliğinden sonra otomatik kontrol yapılır.

| # | Kabul kriteri | Doğrulayan test |
|---|---------------|-----------------|
| AC-5.1 | **Verilen** geçerli dosyalar, **o zaman** çıkış kodu `0`; en az bir test kalırsa `1`. | `test_cli::test_validate_valid_folder_returns_0`; `1` kodu elle doğrulandı (`examples/bilerek-kalan.yaml`) |
| AC-5.2 | **Verilen** geçersiz bir dosya, **o zaman** hiçbir test koşmaz, hatalar listelenir ve çıkış kodu `2` olur. | `test_cli::test_validate_invalid_file_returns_2_and_lists_errors`, `test_cli::test_run_with_invalid_file_does_not_start_browser` |

### US-6 — Takılan testin sonsuza kadar beklememesi
> **Bir test uzmanı olarak**, sayfadaki bir öğe hiç gelmezse testin takılı kalmamasını istiyorum, **böylece** koşular öngörülebilir sürede biter.

| # | Kabul kriteri | Doğrulayan test |
|---|---------------|-----------------|
| AC-6.1 | **Verilen** `stepTimeout: 1000`, **olduğunda** öğe bulunamazsa, **o zaman** adım yaklaşık 1 sn sonra başarısız olur. | `test_worker::test_worker_records_failure_with_screenshot_and_trace` |
| AC-6.2 | Adım ve test süreleri YAML'da ayarlanabilir; geçersiz (negatif) değer reddedilir. | `test_dsl::test_custom_timeouts_and_step_timeout`, `test_dsl::test_negative_timeout` |

## 2.4 Gereksinim önceliklendirmesi (MoSCoW)

| Öncelik | Anlamı | Gereksinimler |
|---------|--------|---------------|
| **Must have** (olmazsa olmaz) | MVP bunlar olmadan teslim edilemez | FR-01 … FR-09, FR-12 |
| **Should have** (olmalı) | Önemli, ama olmasa da sistem kullanılabilir | FR-10, FR-11, FR-13 |
| **Could have** (olabilir) | Zaman kalırsa; değer katar | FR-14 … FR-17 (bonuslar) |
| **Won't have** (bu sürümde yok) | Bilinçli olarak dışarıda bırakıldı | FR-18 |

**Gerekçe:** Ders tanımındaki asgari kapsam "test tanımı, tarayıcı otomasyonu, rapor" olduğu için bu üçünü karşılayan her şey *Must* sayıldı. Web arayüzü (FR-12) teknik olarak API ile ikame edilebilse de canlı demo ve hedef kullanıcı (programcı olmayan test uzmanı) için gerekli olduğundan *Must* yapıldı.

## 2.5 İzlenebilirlik matrisi (gereksinim → hikâye → test)

| Gereksinim | Kullanıcı hikâyesi | Otomatik testler |
|-----------|--------------------|------------------|
| FR-01 | US-1 | `test_dsl` (geçerli tanım, varsayılanlar, örnek dosyalar) |
| FR-02 | US-1 | `test_dsl` (19 hata senaryosu), `test_api::test_invalid_yaml_returns_422_with_turkish_errors`, `test_api::test_validate_endpoint` |
| FR-03 | US-2 | `test_worker::test_worker_runs_passing_test`, `test_demo_site::test_v1_examples_pass` |
| FR-04 | US-6 | `test_worker::test_worker_records_failure_with_screenshot_and_trace`, `test_dsl::test_custom_timeouts_and_step_timeout` |
| FR-05 | US-3 | `test_worker::test_worker_records_failure_with_screenshot_and_trace`, `test_demo_site::test_v2_order_total_bug_is_caught` |
| FR-06 | US-3 | `test_worker` (sonuç JSON'u), `test_db::test_finish_run` |
| FR-07 | US-1 | `test_api::test_update_and_delete_test`, `test_db::test_deleting_test_deletes_its_runs` |
| FR-08 | US-2 | `test_api::test_queue_run_returns_202_and_queued`, `test_db` (kuyruk testleri) |
| FR-09 | US-3 | `test_api::test_run_detail_has_result_and_artifact_urls` |
| FR-10 | US-4 | `test_api::test_list_runs_filters`, `test_db::test_last_run_status_on_test` |
| FR-11 | US-5 | `test_cli` |
| FR-12 | US-1…4 | `test_web` (12 test: formlar, yönlendirmeler, hata gösterimi, XSS kaçışı, rapor, süzgeç); E2E-1…6 (`test_platform_e2e`) |
| FR-13 | US-5 | `.github/workflows/ci.yml`; ilk koşu başarılı (GitHub Actions #1) |
| FR-14 | — | `test_visual` (6 test), E2E-8 `test_visual_regression_flow` |
| FR-19 | — | `test_page_errors` (4 test), `test_web::test_report_shows_page_errors`, E2E-3/E2E-4 |
| FR-20 | — | `test_retries` (5 test), `test_db` (göç, flaky), `test_web::test_flaky_run_shows_badge_and_previous_attempts`, `test_dsl::test_retries_option_and_limits` |
