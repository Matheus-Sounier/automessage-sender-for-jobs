import httpx
import trafilatura
from bs4 import BeautifulSoup
from core.config import CONFIDENCE_CONFIRMED, CONFIDENCE_UNSURE 

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def fetch_and_clean(url: str) -> tuple[str | None, str | None]:
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        print(f"[fetch] falhou ({type(e).__name__}): {url}")
        return None, None

    downloaded = resp.text

    clean_text = trafilatura.extract(
        downloaded,
        include_links=False,
        include_images=False,
        include_tables=False,
        favor_precision=True,
    )

    if not clean_text:
        clean_text = trafilatura.extract(downloaded, include_links=False, include_images=False)

    if not clean_text:
        soup = BeautifulSoup(downloaded, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        clean_text = text if len(text) > 50 else None

    return downloaded, clean_text

def route(signals: dict, llm_result: dict) -> str:
    has_job = llm_result.get("has_job", False)
    confidence = llm_result.get("confidence", 0)

    if has_job and confidence >= CONFIDENCE_CONFIRMED:
        return "job_confirmed"
    if any(signals.values()) or confidence >= CONFIDENCE_UNSURE:
        return "uncertain"
    return "spontaneous"