import httpx
import trafilatura
from bs4 import BeautifulSoup
from typing import Optional

_playwright = None
_shared_browser = None

def start_shared_browser(headless: bool = True):
    """Start a shared Playwright browser for reuse."""
    global _playwright, _shared_browser
    if _shared_browser is not None:
        return _shared_browser
    from playwright.sync_api import sync_playwright

    _playwright = sync_playwright().start()
    _shared_browser = _playwright.chromium.launch(headless=headless)
    return _shared_browser


def stop_shared_browser():
    """Stop the shared Playwright browser if started."""
    global _playwright, _shared_browser
    try:
        if _shared_browser is not None:
            _shared_browser.close()
            _shared_browser = None
    finally:
        if _playwright is not None:
            _playwright.stop()
            _playwright = None


def _use_shared_browser() -> Optional[object]:
    return _shared_browser

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def _fetch_static(url: str) -> str | None:
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPError as e:
        print(f"[fetch] estático falhou ({type(e).__name__}): {url}")
        return None


def _fetch_rendered(url: str) -> tuple[str | None, str | None]:
    """Render page (shared or ephemeral) and return (html, visible_text)."""
    try:
        shared = _use_shared_browser()
        if shared is not None:
            page = shared.new_page(user_agent=HEADERS["User-Agent"])
            page.goto(url, timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            html = page.content()
            visible_text = page.inner_text("body")
            page.close()
            return html, visible_text

        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(user_agent=HEADERS["User-Agent"])
            page.goto(url, timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            html = page.content()
            visible_text = page.inner_text("body")
            browser.close()
            return html, visible_text
    except Exception as e:
        print(f"[fetch] renderizado falhou ({type(e).__name__}): {url}")
        return None, None


def _extract_text(html: str) -> str | None:
    text = trafilatura.extract(html, include_links=False, include_images=False, favor_precision=True)
    if not text:
        text = trafilatura.extract(html, include_links=False, include_images=False)
    if not text:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        raw_text = soup.get_text(separator="\n", strip=True)
        text = raw_text if len(raw_text) > 50 else None
    return text


def fetch_and_clean(url: str, force_render: bool = False) -> tuple[str | None, str | None]:
    downloaded = None if force_render else _fetch_static(url)
    clean_text = _extract_text(downloaded) if downloaded else None

    needs_render = force_render or not clean_text or len(clean_text) < 150
    if needs_render:
        rendered_html, rendered_text = _fetch_rendered(url)
        if rendered_html:
            downloaded = rendered_html

            clean_text = rendered_text if rendered_text else _extract_text(rendered_html)

    return downloaded, clean_text