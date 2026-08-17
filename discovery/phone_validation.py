import re

MANAUS_DDD = "92"

PHONE_FULL_RE = re.compile(r"(?:\+?55\s?)?\(?(\d{2})\)?\s?(\d{4,5})[-\s]?(\d{4})")


def parse_br_phone(raw: str) -> dict | None:
    """Extract DDD and local number from a Brazilian phone string."""
    if not raw:
        return None

    match = PHONE_FULL_RE.search(raw)
    if not match:
        return None

    ddd, first_part, second_part = match.groups()
    local_number = first_part + second_part

    return {
        "ddd": ddd,
        "local_number": local_number,
        "is_mobile": len(local_number) == 9 and local_number.startswith("9"),
    }


def is_manaus_whatsapp(raw: str) -> bool:
    """Return True if number is Manaus WhatsApp (DDD 92 + mobile)."""
    parsed = parse_br_phone(raw)
    if not parsed:
        return False
    return parsed["ddd"] == MANAUS_DDD and parsed["is_mobile"]


def format_whatsapp_international(raw: str) -> str | None:
    """Return +55 92 9XXXX-XXXX if valid, else None."""
    parsed = parse_br_phone(raw)
    if not parsed or not is_manaus_whatsapp(raw):
        return None

    local = parsed["local_number"]
    return f"+55 {parsed['ddd']} {local[:5]}-{local[5:]}"