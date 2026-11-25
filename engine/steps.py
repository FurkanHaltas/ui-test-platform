"""Test adımları — Command (komut) tasarım deseni.

Her adım tipi ayrı bir sınıftır ve hepsi aynı arayüze sahiptir: `execute(page, timeout)`.
Koşucu (runner) hangi adımın ne yaptığını bilmez; sadece sırayla `execute` çağırır.
Yeni bir adım tipi eklemek = dsl.STEP_ARG_TYPES'a tipini eklemek, burada yeni bir sınıf
yazmak ve _build_step'e bir satır eklemek. Koşucuya dokunmak gerekmez.
"""

from pathlib import Path
from typing import Optional

from playwright.sync_api import Page, expect

from engine.dsl import LocatorSpec, StepSpec, TestDefinition, ValueLocatorSpec
from engine.locators import build_locator, describe_locator


def resolve_url(base_url: str, path: str) -> str:
    """'/inventory.html' gibi göreli yolları baseUrl ile birleştirir; tam URL'leri olduğu gibi bırakır."""
    if path.startswith(("http://", "https://")):
        return path
    return base_url.rstrip("/") + "/" + path.lstrip("/")


class Step:
    """Tüm adımların ortak atası. Alt sınıflar `execute` ve `describe` yazar."""

    kind = ""  # YAML'daki adım tipi adı

    def __init__(self, number: int, timeout: Optional[int] = None):
        self.number = number
        self.timeout = timeout  # adıma özel zaman aşımı (ms); None ise testin varsayılanı

    def execute(self, page: Page, timeout: int) -> Optional[str]:
        """Adımı tarayıcıda uygular. Başarısızsa istisna fırlatır.
        Bir dosya üretirse (ekran görüntüsü) yolunu döndürür, yoksa None."""
        raise NotImplementedError

    def describe(self) -> str:
        """Rapor için tek satırlık açıklama."""
        raise NotImplementedError


class GotoStep(Step):
    kind = "goto"

    def __init__(self, number: int, url: str):
        super().__init__(number)
        self.url = url

    def execute(self, page, timeout):
        # Sayfanın HTML'i hazır olunca devam et; resim/dış betik gibi tüm kaynakları ("load")
        # beklemeye gerek yok, çünkü sonraki adımlar öğeleri zaten kendileri bekliyor (auto-wait).
        page.goto(self.url, timeout=timeout, wait_until="domcontentloaded")

    def describe(self):
        return f"goto {self.url}"


class ClickStep(Step):
    kind = "click"

    def __init__(self, number: int, spec: LocatorSpec):
        super().__init__(number, spec.timeout)
        self.spec = spec

    def execute(self, page, timeout):
        # click() öğe görünür, etkin ve sabit olana kadar kendisi bekler (auto-wait).
        build_locator(page, self.spec).click(timeout=timeout)

    def describe(self):
        return f"click {describe_locator(self.spec)}"


class FillStep(Step):
    kind = "fill"

    def __init__(self, number: int, spec: ValueLocatorSpec):
        super().__init__(number, spec.timeout)
        self.spec = spec

    def execute(self, page, timeout):
        build_locator(page, self.spec).fill(self.spec.value, timeout=timeout)

    def describe(self):
        return f'fill {describe_locator(self.spec)} = "{self.spec.value}"'


class ExpectVisibleStep(Step):
    kind = "expectVisible"

    def __init__(self, number: int, spec: LocatorSpec):
        super().__init__(number, spec.timeout)
        self.spec = spec

    def execute(self, page, timeout):
        # expect(...) koşul sağlanana ya da süre dolana kadar tekrar tekrar kontrol eder.
        expect(build_locator(page, self.spec)).to_be_visible(timeout=timeout)

    def describe(self):
        return f"expectVisible {describe_locator(self.spec)}"


class ExpectTextStep(Step):
    kind = "expectText"

    def __init__(self, number: int, spec: ValueLocatorSpec):
        super().__init__(number, spec.timeout)
        self.spec = spec

    def execute(self, page, timeout):
        # Öğenin metni tam olarak bu olmalı (baştaki/sondaki boşluklar yok sayılır).
        expect(build_locator(page, self.spec)).to_have_text(self.spec.value, timeout=timeout)

    def describe(self):
        return f'expectText {describe_locator(self.spec)} = "{self.spec.value}"'


class ExpectUrlStep(Step):
    kind = "expectUrl"

    def __init__(self, number: int, url: str):
        super().__init__(number)
        self.url = url

    def execute(self, page, timeout):
        expect(page).to_have_url(self.url, timeout=timeout)

    def describe(self):
        return f"expectUrl {self.url}"


class ScreenshotStep(Step):
    kind = "screenshot"

    def __init__(self, number: int, path: Path):
        super().__init__(number)
        self.path = path

    def execute(self, page, timeout):
        page.screenshot(path=str(self.path), timeout=timeout)
        return self.path.as_posix()

    def describe(self):
        return f"screenshot {self.path.name}"


def build_steps(test: TestDefinition, output_dir: Path) -> list[Step]:
    """Doğrulanmış adım tariflerini (StepSpec) çalıştırılabilir komut nesnelerine çevirir."""
    return [_build_step(spec, test.base_url, output_dir) for spec in test.steps]


def _build_step(spec: StepSpec, base_url: str, output_dir: Path) -> Step:
    n, args = spec.number, spec.args
    if spec.kind == "goto":
        return GotoStep(n, resolve_url(base_url, args))
    if spec.kind == "expectUrl":
        return ExpectUrlStep(n, resolve_url(base_url, args))
    if spec.kind == "screenshot":
        filename = args if args.endswith(".png") else f"{args}.png"
        return ScreenshotStep(n, output_dir / filename)
    if spec.kind == "click":
        return ClickStep(n, args)
    if spec.kind == "fill":
        return FillStep(n, args)
    if spec.kind == "expectVisible":
        return ExpectVisibleStep(n, args)
    if spec.kind == "expectText":
        return ExpectTextStep(n, args)
    # DSL doğrulaması bilinmeyen tipe izin vermez; buraya gelinirse programlama hatasıdır.
    raise ValueError(f"desteklenmeyen adım tipi: {spec.kind}")
