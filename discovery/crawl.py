from urllib.parse import urljoin, urlparse
import re

from core.constants import CAREER_URL_HINTS

LINK_RE = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)


def find_career_link(base_url: str, raw_html: str) -> str | None:
    """Find a career/work-with-us link in homepage HTML.
    Return absolute URL or None."""
    if not raw_html:
        return None

    links = LINK_RE.findall(raw_html)
    base_domain = urlparse(base_url).netloc

    for link in links:
        absolute = urljoin(base_url, link)
        if urlparse(absolute).netloc != base_domain:
            continue
        if any(hint in absolute.lower() for hint in CAREER_URL_HINTS):
            return absolute

    return None