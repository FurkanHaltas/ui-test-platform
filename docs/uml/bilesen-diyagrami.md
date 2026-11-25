# Bileşen Diyagramı (Aşama 3 sonu)

```mermaid
flowchart LR
    U([Kullanıcı<br/>tarayıcı]) -- "HTML formlar" --> WEB
    X([Diğer sistemler]) -- "HTTP JSON" --> API
    subgraph S1["Süreç 1: uvicorn (tek FastAPI uygulaması)"]
        WEB["web/routes.py<br/>Jinja2 sayfaları"]
        API["api/main.py<br/>JSON API"]
        Static["/artifacts<br/>StaticFiles"]
        Demo["/demo · /demo-v2<br/>demo_site/"]
    end
    subgraph S2["Süreç 2: python -m worker"]
        W["worker/main.py<br/>kuyruk döngüsü"]
        E["engine/<br/>dsl · steps · runner"]
    end
    DB[("data/platform.db<br/>SQLite (WAL)<br/>tests · runs")]
    FS[("artifacts/runs/N/<br/>png · trace.zip")]
    PW["Chromium<br/>(Playwright)"]
    Site(["Hedef site"])

    API -- "INSERT runs (queued)" --> DB
    API -- "SELECT" --> DB
    W -- "UPDATE ... RETURNING<br/>(işi al)" --> DB
    W -- "sonucu yaz" --> DB
    W --> E
    E --> PW --> Site
    E -- "ekran görüntüsü, trace" --> FS
    Static -- "okur" --> FS
    API -. "parse_test (doğrulama)" .-> E
    WEB -- "api/db.py" --> DB
    WEB -. "parse_test" .-> E
    U -. "editör canlı doğrulama<br/>POST /api/validate" .-> API
    PW -. "yerel demo testleri" .-> Demo
```

- API ile worker **ayrı süreçlerdir** ve birbirleriyle doğrudan konuşmaz. Tek ortak noktaları veritabanı ve `artifacts/` klasörüdür.
- Web sayfaları ile JSON API aynı süreçte çalışır ve aynı veritabanı modülünü kullanır (K24).
- Demo sitesi de aynı sunucudan yayınlanır; demo testlerinde "hedef site" odur (K25).
- Aşama 4'te CI bu resme eklenecek.
