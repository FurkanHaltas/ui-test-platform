# Test Motoru — Sınıf Diyagramı

GitHub ve VS Code (Markdown Preview Mermaid eklentisi) bu diyagramı doğrudan çizer.
PNG/SVG için: https://mermaid.live adresine kodu yapıştırıp dışa aktarın.

```mermaid
classDiagram
    direction LR

    %% ---------- dsl.py ----------
    class TestHeader {
        <<Pydantic>>
        +str name
        +str baseUrl
        +int timeout = 60000
        +int stepTimeout = 10000
        +str testIdAttribute = "data-testid"
        +list steps
    }
    class LocatorSpec {
        <<Pydantic>>
        +str? role
        +str? name
        +str? label
        +str? testId
        +str? text
        +str? css
        +int? timeout
        +check_exactly_one_locator()
    }
    class ValueLocatorSpec {
        <<Pydantic>>
        +str value
    }
    class StepSpec {
        +int number
        +str kind
        +StrOrLocator args
    }
    class TestDefinition {
        +str name
        +str base_url
        +int timeout
        +int step_timeout
        +str test_id_attribute
        +str source
        +list~StepSpec~ steps
    }
    class DslError {
        <<Exception>>
        +str source
        +list~str~ errors
    }

    LocatorSpec <|-- ValueLocatorSpec
    TestDefinition "1" *-- "1..*" StepSpec
    StepSpec --> LocatorSpec : args
    TestHeader ..> TestDefinition : doğrulanınca dönüşür

    %% ---------- steps.py (Command pattern) ----------
    class Step {
        <<abstract>>
        +int number
        +int? timeout
        +str kind
        +execute(page, timeout) str?
        +describe() str
        +evidence() dict
    }
    class GotoStep { +str url }
    class ClickStep { +LocatorSpec spec }
    class FillStep { +ValueLocatorSpec spec }
    class ExpectVisibleStep { +LocatorSpec spec }
    class ExpectTextStep { +ValueLocatorSpec spec }
    class ExpectUrlStep { +str url }
    class ScreenshotStep { +Path path }
    class ExpectScreenshotStep {
        +str name
        +Path baseline
        +bool update
        +evidence() dict
    }
    class visual {
        <<module>>
        +compare_images(baseline, actual, diff_out) VisualDiff
    }

    Step <|-- GotoStep
    Step <|-- ClickStep
    Step <|-- FillStep
    Step <|-- ExpectVisibleStep
    Step <|-- ExpectTextStep
    Step <|-- ExpectUrlStep
    Step <|-- ScreenshotStep
    Step <|-- ExpectScreenshotStep
    ExpectScreenshotStep ..> visual
    StepSpec ..> Step : build_steps()

    %% ---------- locators.py ----------
    class locators {
        <<module>>
        +build_locator(page, spec) Locator
        +describe_locator(spec) str
    }
    ClickStep ..> locators
    FillStep ..> locators
    ExpectVisibleStep ..> locators
    ExpectTextStep ..> locators

    %% ---------- results.py ----------
    class RunResult {
        <<Pydantic>>
        +str run_id
        +str test_name
        +str source
        +str base_url
        +str status
        +datetime started_at
        +datetime finished_at
        +int duration_ms
        +str? error
        +str? trace
        +list~StepResult~ steps
        +save_json(path)
        +load_json(path) RunResult
    }
    class StepResult {
        <<Pydantic>>
        +int number
        +str kind
        +str description
        +str status
        +int duration_ms
        +str? error
        +str? screenshot
    }
    RunResult "1" *-- "1..*" StepResult

    %% ---------- runner.py & cli.py ----------
    class runner {
        <<module>>
        +run_tests(tests, headed, artifacts_dir, channel) list~RunResult~
        +run_test(browser, test, artifacts_dir) RunResult
    }
    class cli {
        <<module>>
        +main(argv) int
    }
    cli ..> TestDefinition : load_test()
    cli ..> runner
    runner ..> Step : execute()
    runner ..> RunResult : üretir
```

## Okuma notları
- **Command deseni:** `Step` soyut komuttur. Her alt sınıf tek bir YAML adım tipini temsil eder. `runner` sadece `Step` arayüzünü bilir.
- **İki model katmanı:** Pydantic modelleri (`TestHeader`, `LocatorSpec`) YAML'ı **doğrular**. `TestDefinition`/`StepSpec` doğrulanmış, temiz veridir. `Step` nesneleri ise bu veriyi tarayıcıda **uygular**.
- `?` işareti alanın boş (`None`) olabileceğini gösterir.
- `StrOrLocator`: `StepSpec.args` ya düz metindir (`goto`, `expectUrl`, `screenshot`) ya da `LocatorSpec`/`ValueLocatorSpec`'tir (diğer adımlar).
