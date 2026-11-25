# Yol Haritası

| # | Aşama | Tarih | Durum |
|---|-------|-------|-------|
| 1 | Test motoru (DSL, Playwright koşucu, JSON sonuç, CLI) | 25 Kas – 1 Ara | ✅ |
| 2 | API (FastAPI) + SQLite + worker | 2 – 8 Ara | ✅ |
| 3 | Web arayüzü + rapor ekranı + **yerel demo sitesi** → **MVP** | 9 – 15 Ara | ✅ |
| 4 | Platformun kendi E2E testleri + GitHub (uzak depo) + GitHub Actions + bonus | 16 – 22 Ara | 🟡 GitHub'a yükleme kaldı |
| 5 | Raporu birleştirme (Word/PDF), sunum, prova | 23 – 28 Ara | ⏳ |

Teslim: **28 Aralık 2026** — çalışan yazılım, 12–20 sayfalık doküman, 10–15 dk sunum (uygulama canlı test edilecek).

## Her aşamada yapılacak doküman işleri
Rapor son haftaya bırakılmaz; her aşama kendi bölümünü `rapor/` klasörüne yazarak kapanır. Durum takibi: [rapor/README.md](rapor/README.md).

| Aşama | Doküman görevi |
|-------|----------------|
| Her aşama | Yeni hatalar → `rapor/hata-kaydi.md`; yeni kaynaklar → `rapor/kaynakca.md`; kararlar → `docs/kararlar.md`; gereksinim durumları → `rapor/02-gereksinim-analizi.md` |
| 1–2 | ✅ Proje tanıtımı, gereksinim analizi (hikâyeler, kabul kriterleri, MoSCoW, izlenebilirlik), use case diyagramı |
| 3 | ✅ Web arayüzü ekran görüntüleri (`rapor/ekran-goruntuleri/`); "4. Uygulama geliştirme" taslağı Aşama 5'e kaydı |
| 4 | ✅ "5. Yazılım testleri" (`rapor/05-yazilim-testleri.md`); CI ekran görüntüsü GitHub'a yüklenince |
| 5 | "3. Tasarım" ve "6. Sonuç" bölümlerinin rapor diline çevrilmesi, önemli kod bölümleri, birleştirme, sunum slaytları, demo provası |

## Bonus listesi (MVP sonrası)
- [x] Görsel regresyon (`expectScreenshot`; pixelmatch yerine Pillow, bkz. K31)
- [ ] Kaydedici (Playwright codegen çıktısını YAML'a çeviren dönüştürücü)
- [ ] Yapay zekâ ile hata açıklama
- [ ] Küçük eklemeler: tekrar deneme / flaky işareti, zamanlanmış testler, veri odaklı testler, bildirim
