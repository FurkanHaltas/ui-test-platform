# Bileşen Diyagramı (Aşama 2 sonu)

```mermaid
flowchart LR
    U([Kullanıcı / istemci]) -- "HTTP JSON" --> API
    subgraph S1["Süreç 1: uvicorn"]
        API["api/main.py<br/>FastAPI"]
        Static["/artifacts<br/>StaticFiles"]
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
```

- API ile worker **ayrı süreçlerdir** ve birbirleriyle doğrudan konuşmaz. Tek ortak noktaları veritabanı ve `artifacts/` klasörüdür.
- Aşama 3'te web arayüzü, Aşama 4'te CI bu resme eklenecek.
