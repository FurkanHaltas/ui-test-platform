# Use Case Diyagramı

İki sürüm var:
- **Mermaid:** GitHub/VS Code'da doğrudan görünür. Mermaid'in UML use case türü olmadığı için akış diyagramıyla taklit edildi (oval = use case).
- **PlantUML:** Gerçek UML gösterimi (çöp adam aktörler, sistem sınırı). Rapora koymak için bunu kullanın: kodu <https://www.plantuml.com/plantuml> adresine yapıştırıp PNG/SVG indirin ya da VS Code'un PlantUML eklentisini kullanın.

## Mermaid

```mermaid
flowchart LR
    QA["👤 Test uzmanı"]
    DEV["👤 Geliştirici"]
    PM["👤 Proje yöneticisi"]
    CI["⚙️ CI sistemi<br/>(GitHub Actions)"]
    WRK["⚙️ Worker"]
    SITE["🌐 Hedef web sitesi"]

    subgraph SYS["Otomatik UI Test Platformu"]
        UC1(["Test tanımla (YAML)"])
        UC2(["Test tanımını doğrula"])
        UC3(["Testi düzenle / sil"])
        UC4(["Testi koştur (kuyruğa al)"])
        UC5(["Koşu raporunu görüntüle"])
        UC6(["Hata kanıtını incele<br/>(ekran görüntüsü, trace)"])
        UC7(["Koşu geçmişini listele / süz"])
        UC8(["Testleri komut satırından koştur"])
        UC9(["Kuyruktaki koşuyu işle"])
        UC10(["Adımları tarayıcıda uygula"])
    end

    QA --- UC1
    QA --- UC3
    QA --- UC4
    QA --- UC5
    DEV --- UC6
    DEV --- UC8
    PM --- UC7
    PM --- UC5
    CI --- UC8
    WRK --- UC9

    UC1 -. "«include»" .-> UC2
    UC3 -. "«include»" .-> UC2
    UC8 -. "«include»" .-> UC2
    UC9 -. "«include»" .-> UC10
    UC8 -. "«include»" .-> UC10
    UC6 -. "«extend»<br/>test kaldıysa" .-> UC5
    UC10 --- SITE
```

## PlantUML

```plantuml
@startuml
left to right direction
skinparam actorStyle awesome

actor "Test uzmanı" as QA
actor "Geliştirici" as DEV
actor "Proje yöneticisi" as PM
actor "CI sistemi" as CI <<sistem>>
actor "Worker" as WRK <<sistem>>
actor "Hedef web sitesi" as SITE <<dış sistem>>

rectangle "Otomatik UI Test Platformu" {
  usecase "Test tanımla (YAML)" as UC1
  usecase "Test tanımını doğrula" as UC2
  usecase "Testi düzenle / sil" as UC3
  usecase "Testi koştur\n(kuyruğa al)" as UC4
  usecase "Koşu raporunu görüntüle" as UC5
  usecase "Hata kanıtını incele\n(ekran görüntüsü, trace)" as UC6
  usecase "Koşu geçmişini\nlistele / süz" as UC7
  usecase "Testleri komut\nsatırından koştur" as UC8
  usecase "Kuyruktaki koşuyu işle" as UC9
  usecase "Adımları tarayıcıda uygula" as UC10
}

QA --> UC1
QA --> UC3
QA --> UC4
QA --> UC5
DEV --> UC6
DEV --> UC8
PM --> UC5
PM --> UC7
CI --> UC8
WRK --> UC9

UC1 ..> UC2 : <<include>>
UC3 ..> UC2 : <<include>>
UC8 ..> UC2 : <<include>>
UC9 ..> UC10 : <<include>>
UC8 ..> UC10 : <<include>>
UC6 ..> UC5 : <<extend>>\n(test kaldıysa)
UC10 --> SITE
@enduml
```

## Use case açıklamaları

| Use case | Aktör | Kısa açıklama | Gereksinim |
|----------|-------|---------------|-----------|
| UC1 Test tanımla | Test uzmanı | YAML ile yeni test yazar ve kaydeder. | FR-01, FR-07 |
| UC2 Test tanımını doğrula | (dahil edilen) | Tanım her kayıtta ve koşudan önce doğrulanır; hata Türkçe ve adım numaralı bildirilir. | FR-02 |
| UC3 Testi düzenle / sil | Test uzmanı | Kayıtlı testi günceller ya da siler. | FR-07 |
| UC4 Testi koştur | Test uzmanı | Koşu kuyruğa alınır, istek hemen yanıtlanır. | FR-08 |
| UC5 Koşu raporunu görüntüle | Test uzmanı, Proje yöneticisi | Adım bazında durum, süre, hata. | FR-06, FR-09 |
| UC6 Hata kanıtını incele | Geliştirici | Kalan adımın ekran görüntüsü ve trace dosyası. | FR-05, FR-09 |
| UC7 Koşu geçmişini listele | Proje yöneticisi | Teste/duruma göre süzülmüş geçmiş, testlerin son durumu. | FR-10 |
| UC8 Komut satırından koştur | Geliştirici, CI | `python -m engine run ...`, çıkış koduyla sonuç. | FR-11, FR-13 |
| UC9 Kuyruktaki koşuyu işle | Worker | En eski bekleyen koşuyu atomik olarak alır, sonucu yazar. | FR-08 |
| UC10 Adımları tarayıcıda uygula | (dahil edilen) | Playwright ile Chromium'da adımları uygular, timeout'ları uygular. | FR-03, FR-04 |
