"""Otomatik sayfa hatası yakalama (B1).

Kullanıcı hiçbir şey yazmadan, test koşarken sayfada olan şu hataları kaydeder:
  - console    : sayfanın konsola yazdığı hatalar (console.error)
  - exception  : yakalanmamış JavaScript istisnaları (ör. TypeError)
  - http       : 400 ve üzeri durum koduyla dönen istekler (ör. 404 resim, 500 API)
  - network    : sunucuya hiç ulaşılamayan istekler (DNS, bağlantı reddi)

Bu hatalar "doğrunun ne olduğunu" bilmeden de hata sayılabilen türdendir: her sitede
bir JavaScript istisnası ya da 404 dönen bir kaynak sorun işaretidir (test kâhini
probleminin kısmen aşıldığı alan, bkz. rapor/README.md sınırlılık notu).
"""

from typing import Optional

from playwright.sync_api import ConsoleMessage, Page, Request, Response

from engine.results import PageError

MAX_ERRORS = 50  # bir koşuda en fazla bu kadar farklı hata saklanır (rapor şişmesin)

# Raporlarda (CLI ve web) gösterilen Türkçe tür adları
KIND_LABELS = {
    "console": "Konsol",
    "exception": "JS istisnası",
    "http": "HTTP",
    "network": "Ağ",
}


class PageErrorCollector:
    """Bir sayfaya bağlanır, hataları toplar. Runner her adımdan önce `step`'i günceller."""

    def __init__(self, page: Page):
        self.errors: list[PageError] = []
        self.step: Optional[int] = None  # şu an çalışan adımın numarası
        page.on("console", self._on_console)
        page.on("pageerror", self._on_exception)
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_request_failed)

    # --- Playwright olayları ---------------------------------------------------

    def _on_console(self, msg: ConsoleMessage) -> None:
        if msg.type != "error":
            return
        # Başarısız kaynak yüklemeleri konsola da düşer; onları zaten "http" olarak
        # kaydediyoruz. Aynı hatayı iki kez saymamak için konsoldaki kopyasını atlıyoruz.
        if msg.text.startswith("Failed to load resource"):
            return
        self._add("console", msg.text, msg.location.get("url") or None)

    def _on_exception(self, error) -> None:
        # error: Playwright Error nesnesi. name = istisna türü (TypeError), message = açıklama.
        name = getattr(error, "name", None) or "Error"
        message = (getattr(error, "message", None) or str(error)).splitlines()[0]
        self._add("exception", f"{name}: {message}", None)

    def _on_response(self, response: Response) -> None:
        if response.status >= 400 and not _is_browser_noise(response.url):
            self._add("http", f"HTTP {response.status} {response.status_text}".strip(), response.url)

    def _on_request_failed(self, request: Request) -> None:
        reason = request.failure or "bilinmeyen hata"
        # ERR_ABORTED: sayfa değişirken tarayıcının yarıda bıraktığı istekler; hata değil.
        if "ERR_ABORTED" in reason or _is_browser_noise(request.url):
            return
        self._add("network", f"İstek başarısız: {reason}", request.url)

    # --- Kayıt ----------------------------------------------------------------

    def _add(self, kind: str, message: str, url: Optional[str]) -> None:
        # Aynı hata tekrar tekrar oluyorsa (ör. her saniye) tek satırda sayısını artır.
        for existing in self.errors:
            if (existing.kind, existing.message, existing.url) == (kind, message, url):
                existing.count += 1
                return
        if len(self.errors) < MAX_ERRORS:
            self.errors.append(PageError(kind=kind, message=message, url=url, step=self.step))


def _is_browser_noise(url: str) -> bool:
    """Tarayıcının sayfadan bağımsız, kendiliğinden yaptığı istekler (sitenin hatası değil)."""
    return url.split("?")[0].endswith("/favicon.ico")
