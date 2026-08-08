import re
import unicodedata

def slug(text: str) -> str:
    """Converts free text into a safe filename (no accents/spaces)."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()

def clean_json_markdown(text: str) -> str:
    """Removes code block backticks (```json ... ```) that the LLM sometimes returns."""
    return re.sub(r"^```json|```$", "", text.strip()).strip()

def clean_phone(number: str) -> str:
    """Removes any non-digit characters from a phone number (spaces, +, -, parentheses)."""
    return re.sub(r"\D", "", number)

def normalize_br_number(number: str) -> str:
    digits = clean_phone(number)
    if not digits.startswith("55"):
        digits = "55" + digits
    return digits