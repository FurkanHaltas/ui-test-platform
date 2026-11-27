"""Test tanım dili (DSL) v1: YAML dosyasını okur, doğrular ve Python nesnelerine çevirir.

Örnek:
    name: Başarılı giriş
    baseUrl: https://www.saucedemo.com
    steps:
      - goto: /
      - click: { role: button, name: Login }

Doğrulama iki katmanlıdır:
  1. Kök alanlar (name, baseUrl, timeout ...) Pydantic modeli `TestHeader` ile.
  2. Her adım tek tek: önce adım tipi bilinen bir tip mi, sonra içeriği
     o tipin Pydantic modeline uyuyor mu.
Böylece hata mesajında "3. adım (fill)" gibi net bir konum verebiliyoruz.
"""

import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, PositiveInt, ValidationError, field_validator, model_validator

# Locator (öğe bulma) türleri, öncelik sırasıyla. "name" sadece "role" ile birlikte kullanılır.
LOCATOR_KINDS = ["role", "label", "testId", "text", "css"]


class DslError(Exception):
    """YAML test dosyası geçersiz olduğunda fırlatılır. `errors` Türkçe mesaj listesidir."""

    def __init__(self, source: str, errors: list[str]):
        self.source = source
        self.errors = errors
        lines = "\n".join(f"  - {e}" for e in errors)
        super().__init__(f"{source} geçersiz:\n{lines}")


# ---------------------------------------------------------------------------
# Pydantic modelleri
# ---------------------------------------------------------------------------

class LocatorSpec(BaseModel):
    """Sayfadaki bir öğenin nasıl bulunacağı. Tam olarak bir locator türü içermeli."""

    model_config = ConfigDict(extra="forbid")

    role: Optional[str] = None
    name: Optional[str] = None  # sadece role ile: erişilebilir isim (ör. buton yazısı)
    label: Optional[str] = None
    testId: Optional[str] = None
    text: Optional[str] = None
    css: Optional[str] = None
    timeout: Optional[PositiveInt] = None  # bu adıma özel zaman aşımı (ms)

    @model_validator(mode="after")
    def check_exactly_one_locator(self):
        used = [kind for kind in LOCATOR_KINDS if getattr(self, kind) is not None]
        if len(used) == 0:
            raise ValueError(
                "öğeyi bulmak için bir locator gerekli (role, label, testId, text veya css)"
            )
        if len(used) > 1:
            raise ValueError(
                f"tam olarak bir locator kullanılmalı, ama birden fazla verilmiş: {', '.join(used)}"
            )
        if self.name is not None and self.role is None:
            raise ValueError("'name' alanı sadece 'role' ile birlikte kullanılabilir")
        return self


class ValueLocatorSpec(LocatorSpec):
    """fill ve expectText için: locator + bir metin değeri."""

    value: str

    @field_validator("value", mode="before")
    @classmethod
    def numbers_to_text(cls, v):
        # YAML'da `value: 12345` sayı olarak okunur; kullanıcı dostu olsun diye metne çeviriyoruz.
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return str(v)
        return v


class TestHeader(BaseModel):
    """YAML dosyasının kök alanları."""

    model_config = ConfigDict(extra="forbid")

    name: str
    baseUrl: str
    timeout: PositiveInt = 60_000  # testin tamamı için üst sınır (ms)
    stepTimeout: PositiveInt = 10_000  # adım başına varsayılan zaman aşımı (ms)
    testIdAttribute: str = "data-testid"  # testId locator'ının baktığı HTML özniteliği
    failOnPageErrors: bool = False  # True: sayfada JS/ağ hatası olursa test kalır (B1)
    retries: int = Field(0, ge=0, le=5)  # kalan test en fazla kaç kez yeniden denensin (B2)
    # Veri odaklı test (B3): her satır, ${alan} yer tutucuları doldurularak ayrı koşturulur.
    data: Optional[list[dict[str, Any]]] = None
    steps: list[Any]

    @field_validator("baseUrl")
    @classmethod
    def check_base_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("'baseUrl' http:// veya https:// ile başlamalı")
        return v

    @field_validator("data")
    @classmethod
    def check_data_rows(cls, v):
        if v is None:
            return v
        if len(v) == 0:
            raise ValueError("'data' tablosu en az bir satır içermeli")
        if len(v) > MAX_DATA_ROWS:
            raise ValueError(f"'data' tablosu en fazla {MAX_DATA_ROWS} satır olabilir")
        rows = []
        for number, row in enumerate(v, start=1):
            if not row:
                raise ValueError(f"'data' tablosunun {number}. satırı boş")
            for key, value in row.items():
                if isinstance(value, (dict, list)):
                    raise ValueError(f"'data' tablosunun {number}. satırında '{key}' tek bir değer olmalı")
            # Bütün değerleri metne çevir (YAML'da 123 sayı, boş değer None olarak okunur).
            rows.append({k: "" if val is None else str(val) for k, val in row.items()})
        return rows

    @field_validator("steps")
    @classmethod
    def check_steps_not_empty(cls, v: list) -> list:
        if len(v) == 0:
            raise ValueError("'steps' listesi boş olamaz, en az bir adım gerekli")
        return v


# Her adım tipinin içeriğinin nasıl görünmesi gerektiği.
# `str` olanlar düz metin alır (ör. `goto: /login`), diğerleri bir sözlük alır.
STEP_ARG_TYPES: dict[str, Any] = {
    "goto": str,
    "click": LocatorSpec,
    "fill": ValueLocatorSpec,
    "expectVisible": LocatorSpec,
    "expectText": ValueLocatorSpec,
    "expectUrl": str,
    "screenshot": str,
    "expectScreenshot": str,  # görsel regresyon: referans görüntüyle karşılaştır
}


@dataclass
class StepSpec:
    """Doğrulanmış tek bir adım. `args` ya metin ya da LocatorSpec/ValueLocatorSpec."""

    number: int  # 1'den başlayan sıra numarası
    kind: str  # adım tipi, ör. "click"
    args: Union[str, LocatorSpec, ValueLocatorSpec]


MAX_DATA_ROWS = 50
PLACEHOLDER = re.compile(r"\$\{(\w+)\}")  # ${kullanici} gibi yer tutucular


@dataclass
class TestDefinition:
    """Doğrulanmış, koşturulmaya hazır test tanımı."""

    __test__ = False  # pytest bu sınıfı test sanmasın

    name: str
    base_url: str
    timeout: int
    step_timeout: int
    test_id_attribute: str
    steps: list[StepSpec]
    fail_on_page_errors: bool = False
    retries: int = 0
    source: str = "<metin>"
    data: list[dict[str, str]] = field(default_factory=list)  # veri tablosu (B3)
    data_row: Optional[dict[str, str]] = None  # bu test bir satırın kopyasıysa o satır

    def expand_rows(self) -> list["TestDefinition"]:
        """Veri tablosunun her satırı için yer tutucuları doldurulmuş ayrı bir test üretir."""
        return [
            replace(self, name=f"{self.name} [{number}. satır]", data=[], data_row=row,
                    steps=[_substitute(step, row) for step in self.steps])
            for number, row in enumerate(self.data, start=1)
        ]


# ---------------------------------------------------------------------------
# Yükleme ve doğrulama
# ---------------------------------------------------------------------------

def load_test(path: Union[str, Path]) -> TestDefinition:
    """YAML dosyasını okuyup doğrular. Hata varsa DslError fırlatır."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise DslError(str(path), [f"dosya okunamadı: {e.strerror}"])
    return parse_test(text, source=str(path))


def parse_test(text: str, source: str = "<metin>") -> TestDefinition:
    """YAML metnini doğrular ve TestDefinition döndürür. Hata varsa DslError fırlatır."""
    # 1) YAML sözdizimi
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        line = ""
        hint = ""
        mark = getattr(e, "problem_mark", None)
        if mark is not None:
            line = f" (satır {mark.line + 1}, sütun {mark.column + 1})"
            # Süslü parantez içinde tırnaksız ${alan}: YAML '{' karakterini iç içe sözlük sanar.
            lines = text.splitlines()
            if mark.line < len(lines) and "${" in lines[mark.line]:
                hint = ' — süslü parantez içinde ${...} kullanırken değeri tırnağa alın, ör. value: "${kullanici}"'
        raise DslError(source, [f"YAML sözdizimi hatası{line}: {getattr(e, 'problem', e)}{hint}"])

    if not isinstance(data, dict):
        raise DslError(source, ["dosyanın en üstünde name, baseUrl ve steps alanları olmalı"])

    # 2) Kök alanlar
    try:
        header = TestHeader.model_validate(data)
    except ValidationError as e:
        raise DslError(source, [_translate_error(err) for err in e.errors()])

    # 3) Adımlar: tüm hataları toplayıp birlikte gösteriyoruz
    steps: list[StepSpec] = []
    errors: list[str] = []
    for number, raw in enumerate(header.steps, start=1):
        try:
            steps.append(_parse_step(number, raw))
        except ValueError as e:
            errors.append(str(e))
    if errors:
        raise DslError(source, errors)

    # 4) Yer tutucular: her ${alan} veri tablosunun her satırında olmalı
    errors = _check_placeholders(steps, header.data)
    if errors:
        raise DslError(source, errors)

    return TestDefinition(
        name=header.name,
        base_url=header.baseUrl,
        timeout=header.timeout,
        step_timeout=header.stepTimeout,
        test_id_attribute=header.testIdAttribute,
        fail_on_page_errors=header.failOnPageErrors,
        retries=header.retries,
        data=header.data or [],
        steps=steps,
        source=source,
    )


def _parse_step(number: int, raw: Any) -> StepSpec:
    """Tek bir adımı doğrular. Sorun varsa konumu belirten bir ValueError fırlatır."""
    where = f"{number}. adım"

    # Her adım tek anahtarlı bir sözlük olmalı: `- click: {...}`
    if not isinstance(raw, dict) or len(raw) != 1:
        raise ValueError(
            f"{where}: her adım tek bir adım tipi içermeli (ör. '- click: {{...}}'), "
            f"bulunan: {raw!r}"
        )

    kind, value = next(iter(raw.items()))
    if kind not in STEP_ARG_TYPES:
        known = ", ".join(STEP_ARG_TYPES)
        raise ValueError(f"{where}: bilinmeyen adım tipi '{kind}'. Geçerli tipler: {known}")

    where = f"{number}. adım ({kind})"
    expected = STEP_ARG_TYPES[kind]

    if expected is str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{where}: boş olmayan bir metin bekleniyor, bulunan: {value!r}")
        return StepSpec(number, kind, value.strip())

    if not isinstance(value, dict):
        raise ValueError(
            f"{where}: süslü parantezli bir sözlük bekleniyor (ör. {{ role: button, name: Login }}), "
            f"bulunan: {value!r}"
        )
    try:
        args = expected.model_validate(value)
    except ValidationError as e:
        details = "; ".join(_translate_error(err) for err in e.errors())
        raise ValueError(f"{where}: {details}")
    return StepSpec(number, kind, args)


def _step_texts(step: StepSpec) -> list[str]:
    """Bir adımın içindeki bütün metin değerleri (yer tutucu aramak ve doldurmak için)."""
    if isinstance(step.args, str):
        return [step.args]
    return [v for v in step.args.model_dump().values() if isinstance(v, str)]


def _check_placeholders(steps: list[StepSpec], data: Optional[list[dict[str, str]]]) -> list[str]:
    errors = []
    for step in steps:
        where = f"{step.number}. adım ({step.kind})"
        names = {name for text in _step_texts(step) for name in PLACEHOLDER.findall(text)}
        for name in sorted(names):
            if not data:
                errors.append(f"{where}: '${{{name}}}' kullanılmış ama 'data' tablosu tanımlı değil")
                continue
            missing = [str(i) for i, row in enumerate(data, start=1) if name not in row]
            if missing:
                errors.append(f"{where}: '${{{name}}}' veri tablosunun {', '.join(missing)}. satırında yok")
    return errors


def _substitute(step: StepSpec, row: dict[str, str]) -> StepSpec:
    """Adımdaki ${alan} yer tutucularını satırdaki değerlerle değiştirir."""
    def fill(text: str) -> str:
        return PLACEHOLDER.sub(lambda m: row[m.group(1)], text)

    if isinstance(step.args, str):
        return StepSpec(step.number, step.kind, fill(step.args))
    updates = {k: fill(v) for k, v in step.args.model_dump().items() if isinstance(v, str)}
    return StepSpec(step.number, step.kind, step.args.model_copy(update=updates))


def _translate_error(err: dict) -> str:
    """Pydantic'in İngilizce hata kaydını kısa bir Türkçe mesaja çevirir."""
    field = ".".join(str(p) for p in err["loc"])
    kind = err["type"]
    if kind == "missing":
        return f"'{field}' alanı zorunlu ama verilmemiş"
    if kind == "extra_forbidden":
        if err.get("input") is None:
            # `{ value: Cad. No 1, Ankara }` -> YAML virgülden sonrasını değeri boş yeni bir alan sanar.
            return (f"bilinmeyen alan '{field}' — değerde virgül varsa değeri tırnak içine alın, "
                    f'ör. value: "a, b"')
        return f"bilinmeyen alan '{field}'"
    if kind == "string_type":
        return f"'{field}' metin olmalı"
    if kind in ("int_type", "int_parsing", "int_from_float"):
        return f"'{field}' tam sayı olmalı (milisaniye)"
    if kind in ("greater_than_equal", "less_than_equal"):
        limit = err["ctx"].get("ge", err["ctx"].get("le"))
        word = "küçük" if kind == "greater_than_equal" else "büyük"
        return f"'{field}' {limit} değerinden {word} olamaz"
    if kind == "greater_than":
        return f"'{field}' sıfırdan büyük olmalı"
    if kind == "list_type":
        return f"'{field}' bir liste olmalı (her satır '- ' ile başlar)"
    if kind == "value_error":
        # Kendi yazdığımız ValueError mesajları zaten Türkçe.
        return str(err["ctx"]["error"])
    return f"'{field}': {err['msg']}"
