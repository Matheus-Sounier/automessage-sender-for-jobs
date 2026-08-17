import re
import html
from bs4 import BeautifulSoup
from discovery.phone_validation import is_manaus_whatsapp, format_whatsapp_international

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
MAILTO_RE = re.compile(r'href=["\']mailto:([^"\'?]+)', re.IGNORECASE)
CF_EMAIL_RE = re.compile(r'data-cfemail=["\']([a-f0-9]+)["\']', re.IGNORECASE)

GENERIC_PREFIXES = {"contato", "atendimento", "sac", "suporte", "info", "comercial"}
GENERIC_USERNAMES = {"email", "example", "exemplo", "teste", "test", "seu", "seu.email", "nome", "name"}

PHONE_CANDIDATES_RE = re.compile(r"(?:\+?55\s?)?\(?\d{2}\)?\s?\d{4,5}[-\s]?\d{4}")


def decode_cf_email(encoded: str) -> str | None:
    """Decode Cloudflare-protected email."""
    try:
        r = int(encoded[:2], 16)
        email = "".join(
            chr(int(encoded[i:i + 2], 16) ^ r)
            for i in range(2, len(encoded), 2)
        )
        return email
    except (ValueError, IndexError):
        return None


def extract_email(clean_text: str, raw_html: str = "") -> str | None:
    candidates: list[str] = []
    sources: dict[str, set[str]] = {}

    def add_candidate(email: str, src: str):
        email = email.strip()
        if not email:
            return
        candidates.append(email)
        sources.setdefault(email, set()).add(src)

    attr_emails = set()
    if raw_html:
        for encoded in CF_EMAIL_RE.findall(raw_html):
            decoded = decode_cf_email(encoded)
            if decoded:
                add_candidate(decoded, "cf")

        for m in MAILTO_RE.findall(raw_html):
            add_candidate(m, "mailto")

        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            visible = soup.get_text(" ") or ""
            for m in EMAIL_RE.findall(visible):
                add_candidate(m, "html_text")

            attr_texts = []
            for tag in soup.find_all(["input", "textarea", "option"]):
                for attr in ("placeholder", "value", "aria-label", "title"):
                    v = tag.get(attr)
                    if v:
                        attr_texts.append(v)
            if attr_texts:
                joined = " ".join(attr_texts)
                for m in EMAIL_RE.findall(joined):
                    attr_emails.add(m)
                    add_candidate(m, "attr")
        except Exception:
            pass

    if clean_text:
        for m in EMAIL_RE.findall(clean_text):
            add_candidate(m, "text")

    if not candidates:
        return None

    for c in candidates:
        prefix = c.split("@")[0].lower()
        if any(k in prefix for k in ("rh", "talento", "vaga", "carreira", "recruta")):
            return c

    def is_generic_username(email: str) -> bool:
        user = email.split("@")[0].lower()
        return user in GENERIC_USERNAMES or user.startswith("email") or user in GENERIC_PREFIXES

    non_generic = [c for c in candidates if not is_generic_username(c)]
    if non_generic:
        for c in non_generic:
            srcs = sources.get(c, set())
            if "attr" not in srcs:
                return c
        return non_generic[0]

    for c in candidates:
        srcs = sources.get(c, set())
        if "mailto" in srcs or "cf" in srcs:
            return c

    return None


def extract_phone(clean_text: str, raw_html: str = "") -> str | None:
    """Return formatted phone (prefer Manaus WhatsApp) or None."""
    text = (clean_text or "") + " " + (raw_html or "")
    candidates = PHONE_CANDIDATES_RE.findall(text)

    if not candidates:
        return None

    for c in candidates:
        formatted = format_whatsapp_international(c)
        if formatted:
            return formatted

    return None