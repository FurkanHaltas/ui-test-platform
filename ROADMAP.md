# Yol Haritası

| # | Aşama | Tarih | Durum |
|---|-------|-------|-------|
| 1 | Test motoru (DSL, Playwright koşucu, JSON sonuç, CLI) | 25 Kas – 1 Ara | ✅ |
| 2 | API (FastAPI) + SQLite + worker | 2 – 8 Ara | ✅ |
| 3 | Web arayüzü + rapor ekranı + **yerel demo sitesi** → **MVP** | 9 – 15 Ara | ✅ |
| 4 | Platformun kendi E2E testleri + GitHub (uzak depo) + GitHub Actions + bonus | 16 – 22 Ara | ✅ |
| B | Bonuslar B1–B6 (bkz. aşağıdaki bonus yol haritası) | 30 Kas – 14 Ara | 🚧 |
| 5 | Raporu birleştirme (Word/PDF), sunum, prova | **15** – 28 Ara | ⏳ |

Teslim: **28 Aralık 2026** — çalışan yazılım, 12–20 sayfalık doküman, 10–15 dk sunum (uygulama canlı test edilecek).

## Her aşamada yapılacak doküman işleri
Rapor son haftaya bırakılmaz; her aşama kendi bölümünü `rapor/` klasörüne yazarak kapanır. Durum takibi: [rapor/README.md](rapor/README.md).

| Aşama | Doküman görevi |
|-------|----------------|
| Her aşama | Yeni hatalar → `rapor/hata-kaydi.md`; yeni kaynaklar → `rapor/kaynakca.md`; kararlar → `docs/kararlar.md`; gereksinim durumları → `rapor/02-gereksinim-analizi.md` |
| 1–2 | ✅ Proje tanıtımı, gereksinim analizi (hikâyeler, kabul kriterleri, MoSCoW, izlenebilirlik), use case diyagramı |
| 3 | ✅ Web arayüzü ekran görüntüleri (`rapor/ekran-goruntuleri/`); "4. Uygulama geliştirme" taslağı Aşama 5'e kaydı |
| 4 | ✅ "5. Yazılım testleri" (`rapor/05-yazilim-testleri.md`); CI ekran görüntüsü |
| 5 | "3. Tasarım" ve "6. Sonuç" bölümlerinin rapor diline çevrilmesi, önemli kod bölümleri, birleştirme, sunum slaytları, demo provası |

## Bonus listesi (MVP sonrası)
- [x] Görsel regresyon (`expectScreenshot`; pixelmatch yerine Pillow, bkz. K31)
- [x] B1 Otomatik sayfa hatası yakalama (konsol + ağ), 27.11.2026, bkz. K32
- [x] B2 Tekrar deneme ve kararsız (flaky) test işareti, 27.11.2026, bkz. K33
- [x] B3 Veri odaklı testler, 27.11.2026, bkz. K34
- [ ] B4 Kaydedici (Playwright codegen → YAML)
- [ ] B5 Zamanlanmış testler + bildirim
- [ ] B6 Yapay zekâ ile hata açıklama (isteğe bağlı)

## Bonus yol haritası (onaylandı 27.11.2026)

**Zaman kutusu kuralı:** Aşama 5 (rapor + sunum) **en geç 15 Aralık'ta** başlar; bu tarih kaymaz. O güne yetişmeyen bonus kesilir ve rapora "gelecekte yapılabilecek iyileştirmeler" olarak yazılır. Bonuslar notlanan teslimi (doküman, sunum) riske atamaz.

**Her bonusun "bitti" tanımı:** kendi otomatik testleri yazıldı · tüm testler ve CI yeşil · demo sitesinde canlı gösterilebilir bir senaryo var · `docs/kararlar.md`, `rapor/02-gereksinim-analizi.md` (yeni FR satırı), gerekiyorsa hata kaydı güncellendi · commit + push.

| # | Bonus | Tahmini süre | Takvim | Savunma/demo değeri | Bağımlılık |
|---|-------|-------------|--------|---------------------|-----------|
| B1 | Otomatik sayfa hatası yakalama | 0,5–1 gün | 30 Kas – 1 Ara | ★★★ "Siteyi gezip hata bulamıyor" eleştirisine cevap | — |
| B2 | Tekrar deneme + flaky işareti | 1 gün | 2 – 3 Ara | ★★ Test mühendisliği bilgisi | — |
| B3 | Veri odaklı testler | 1–1,5 gün | 4 – 6 Ara | ★★ Tek testle çok senaryo | — |
| B4 | Kaydedici (codegen → YAML) | 2 gün | 7 – 10 Ara | ★★★ "Tıklayarak test oluştur" | — |
| B5 | Zamanlanmış testler + bildirim | 1–1,5 gün | 11 – 12 Ara | ★★ Sürekli izleme | B2 önerilir (kararsız testler sahte alarm üretmesin) |
| B6 | Yapay zekâ ile hata açıklama | 1,5 gün | 13 – 14 Ara | ★★★ Etkileyici ama dış servise bağlı | İnternet + API anahtarı; isteğe bağlı |

Toplam ~8–9 iş günü, 15 günlük pencereye tampon payıyla sığar. Sıralama: değer/efor oranı yüksek ve dış bağımlılığı olmayanlar önce; dış servise bağlı olan (B6) en sonda ve kesilmeye en açık olan.

### B1 — Otomatik sayfa hatası yakalama
- **Ne:** Kullanıcı hiçbir şey yazmadan, her koşuda sayfadaki JavaScript hataları (`console.error`, yakalanmamış istisnalar) ve başarısız ağ istekleri (4xx/5xx yanıtlar, ulaşılamayan kaynaklar) kaydedilir. Raporda "Sayfa hataları" kutusunda gösterilir.
- **Nasıl:** Runner'da Playwright olayları dinlenir: `page.on("console")`, `page.on("pageerror")`, `page.on("response")`, `page.on("requestfailed")`. `RunResult`'a hata listeleri eklenir.
- **Karar noktası:** Varsayılan davranış **uyarı** (test kalmaz). YAML'da `failOnPageErrors: true` yazılırsa test kalır.
- **Demo:** Sürüm 2.0'a bilerek bir JavaScript hatası ve kırık bir resim eklenir. 1.0 temiz, 2.0'da kimse sormadan iki sayfa hatası raporlanır.
- **Test:** Yerel sayfada bilinçli hata → yakalandığını doğrulayan entegrasyon testi, rapor ekranı için web testi.

### B2 — Tekrar deneme ve kararsız (flaky) test işareti
- **Ne:** YAML'da `retries: 2`. Kalan test temiz bir oturumla baştan tekrar denenir. Sonradan geçerse sonuç "Geçti" olur ama **"Kararsız"** rozetiyle işaretlenir. Her denemenin adımları ve kanıtları raporda saklanır.
- **Neden önemli:** Tekrar deneme hataları gizlememeli, görünür kılmalı. Kararsız test ayrı bir bilgi olarak raporlanır (K7'deki "flaky test" tartışmasının devamı).
- **Demo:** Demo sitesine yanıt süresi rastgele değişen küçük bir sayfa eklenir; kısa timeout'lu test bazen ilk denemede kalır, ikincide geçer → "Kararsız".
- **Test:** İlk denemede kalan, ikincide geçen bir senaryo; hiç geçmeyen bir senaryo (tüm denemeler kaydedilir).

### B3 — Veri odaklı testler
- **Ne:** Bir test birden fazla veri satırıyla koşar. YAML'da `data:` tablosu, adımlarda `${alan}` yer tutucuları:
  ```yaml
  data:
    - { kullanici: demo,    sifre: demo123, beklenen: Ürünler }
    - { kullanici: kilitli, sifre: demo123, beklenen: Bu hesap kilitlendi... }
  ```
- **Nasıl:** DSL doğrulaması yer tutucuların tabloda olduğunu kontrol eder (Türkçe hata: "3. adım: `${sifre}` veri tablosunda yok"). Her satır ayrı bir alt koşu olarak raporlanır.
- **Demo:** Tek giriş testiyle geçerli, kilitli ve yanlış şifreli kullanıcı aynı anda sınanır.
- **Test:** DSL birim testleri (yer tutucu, eksik alan), satır başına ayrı sonuç üreten entegrasyon testi.

### B4 — Kaydedici (codegen → YAML)
- **Ne:** `python -m engine record http://127.0.0.1:8000/demo -o yeni.yaml`. Tarayıcı açılır, kullanıcı siteyi gezer; kapatınca YAML test hazırdır.
- **Nasıl:** Playwright'ın kendi kaydedicisi (`playwright codegen --target python --channel chrome`) Python kodu üretir. Bu kod Python'un `ast` modülüyle ağaç olarak okunur ve `page.get_by_role("button", name="Giriş yap").click()` gibi çağrılar `click: { role: button, name: Giriş yap }` adımlarına çevrilir. Çevrilemeyen satırlar YAML'a yorum olarak eklenir; bilgi kaybolmaz. Raporun "Temel algoritmalar" bölümü için iyi bir malzeme.
- **Risk:** Bu makinede görünür mod için `--channel chrome` şart (H-02).
- **Demo:** Sunumda canlı: demo sitesinde birkaç tıklama → YAML → editöre yapıştır → koştur.
- **Test:** Örnek codegen çıktılarını YAML'a çeviren birim testleri (tarayıcısız).

### B5 — Zamanlanmış testler + bildirim
- **Ne:** Test sayfasında "her N dakikada bir koştur" ayarı. Koşu kalınca ya da tekrar düzelince bir webhook adresine (Discord/Slack/Teams uyumlu JSON) bildirim gönderilir.
- **Nasıl:** `tests` tablosuna zamanlama sütunu; worker döngüsü vadesi gelen testleri kuyruğa ekler. Bildirim adresi `UITP_WEBHOOK_URL` ortam değişkeniyle verilir; yoksa bildirimler sadece web arayüzündeki bir "Bildirimler" listesinde görünür (internetsiz demo için).
- **Test:** Saat sahtelenerek (vadesi gelmiş / gelmemiş) zamanlayıcı birim testleri; yerel sahte webhook sunucusuyla bildirim testi.

### B6 — Yapay zekâ ile hata açıklama (isteğe bağlı)
- **Ne:** Rapor sayfasında "Hatayı açıkla" butonu. Kalan adım, hata mesajı, YAML ve sayfanın metin özeti bir dil modeline (Claude API) gönderilir; Türkçe sade bir açıklama ve düzeltme önerisi döner.
- **Koşullar:** API anahtarı (`ANTHROPIC_API_KEY`) yoksa buton görünmez, platformun geri kalanı etkilenmez. Testlerde API sahtelenir (mock); CI dış servise gitmez.
- **Riskler:** İnternet ve API anahtarı gerektirir, küçük bir maliyeti vardır, test edilen sitenin içeriği dış servise gönderilir (raporda belirtilmeli). Sunumda internet yoksa önceden alınmış bir açıklama gösterilir.
