"""Render a local HTML letter as one full-height JPEG."""
from pathlib import Path


def screenshot_letter(html_filename=None, output=None, width=1280, quality=95, browser="auto") -> Path:
    if not 1 <= width <= 16384 or not 1 <= quality <= 100:
        raise ValueError("Ширина должна быть от 1 до 16384, качество — от 1 до 100.")
    if browser not in {"auto", "chromium", "msedge", "chrome"}:
        raise ValueError("Браузер должен быть auto, chromium, msedge или chrome.")
    if html_filename is None:
        candidates = sorted(Path.cwd().glob("*.html"))
        if not candidates:
            raise FileNotFoundError("HTML письма не найден в текущей папке.")
        if len(candidates) != 1:
            raise ValueError("Найдено несколько HTML-файлов. Укажите --html-filename.")
        source = candidates[0]
    else:
        source = Path(html_filename).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"HTML письма не найден: {source}")
    target = Path(output).resolve() if output is not None else source.with_suffix(".jpg")
    if target.suffix.lower() not in {".jpg", ".jpeg"}:
        raise ValueError("Выходной файл должен иметь расширение .jpg или .jpeg.")

    try:
        from playwright.sync_api import Error as PlaywrightError, sync_playwright
    except ImportError as exc:
        raise RuntimeError("Не установлен Playwright. Обновите GMU или выполните: pip install playwright") from exc

    try:
        with sync_playwright() as playwright:
            channels = ["chromium", "msedge", "chrome"] if browser == "auto" else [browser]
            launched = None
            for channel in channels:
                try:
                    options = {} if channel == "chromium" else {"channel": channel}
                    launched = playwright.chromium.launch(headless=True, **options)
                    break
                except PlaywrightError:
                    continue
            if launched is None:
                raise RuntimeError(
                    "Не удалось запустить браузер для снимка. Установите Chromium: "
                    "playwright install chromium. Можно использовать установленный Edge или Chrome "
                    "через --browser msedge или --browser chrome."
                )
            try:
                page = launched.new_page(viewport={"width": width, "height": 800}, device_scale_factor=1)
                page.set_default_timeout(30000)
                page.goto(source.as_uri(), wait_until="load", timeout=30000)
                # Force lazy images to load even below the initial viewport.
                page.evaluate("""() => {
                    for (const image of document.images) image.loading = 'eager';
                }""")
                page.wait_for_function("Array.from(document.images).every(image => image.complete)")
                failed = page.evaluate("""() => Array.from(document.images)
                    .filter(image => image.getAttribute('src') && image.naturalWidth === 0)
                    .map(image => image.getAttribute('src'))""")
                if failed:
                    raise RuntimeError("Не загрузились изображения письма: " + ", ".join(failed[:5]))
                page.wait_for_function("document.fonts.status === 'loaded'")
                page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
                # Render before writing, so failures do not truncate an existing JPEG.
                screenshot = page.screenshot(type="jpeg", full_page=True, quality=quality,
                                             animations="disabled", timeout=30000)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(screenshot)
            finally:
                launched.close()
    except PlaywrightError as exc:
        raise RuntimeError(f"Не удалось снять всё письмо: {exc}") from exc
    return target
