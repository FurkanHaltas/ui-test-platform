"""LocatorSpec (YAML'daki öğe tarifi) -> Playwright Locator dönüşümü."""

from playwright.sync_api import Locator, Page

from engine.dsl import LocatorSpec


def build_locator(page: Page, spec: LocatorSpec) -> Locator:
    """YAML'daki locator tarifine göre Playwright'ın ilgili get_by_* metodunu çağırır.

    Sıra, Playwright'ın önerdiği öncelik sırasıdır: kullanıcının gördüğüne en yakın
    olan (role, label) önce, en kırılgan olan (css) en son.
    """
    if spec.role is not None:
        # role: button, name: Login  ->  page.get_by_role("button", name="Login")
        return page.get_by_role(spec.role, name=spec.name)
    if spec.label is not None:
        return page.get_by_label(spec.label)
    if spec.testId is not None:
        return page.get_by_test_id(spec.testId)
    if spec.text is not None:
        return page.get_by_text(spec.text)
    # DSL doğrulaması en az bir locator olduğunu garanti ettiği için kalan tek seçenek css.
    return page.locator(spec.css)


def describe_locator(spec: LocatorSpec) -> str:
    """Rapor ve hata mesajları için okunur kısa açıklama, ör. role=button[name="Login"]."""
    if spec.role is not None:
        if spec.name is not None:
            return f'role={spec.role}[name="{spec.name}"]'
        return f"role={spec.role}"
    if spec.label is not None:
        return f'label="{spec.label}"'
    if spec.testId is not None:
        return f'testId="{spec.testId}"'
    if spec.text is not None:
        return f'text="{spec.text}"'
    return f"css={spec.css}"
