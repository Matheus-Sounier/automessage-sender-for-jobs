import base64
import httpx

from core.config import EVOLUTION_API_URL, AUTHENTICATION_API_KEY, EVOLUTION_INSTANCE

HEADERS = {
    "apikey": AUTHENTICATION_API_KEY,
    "Content-Type": "application/json",
}

def send_text(number: str, text: str) -> dict:
    """Sends a plain text message to a WhatsApp number via Evolution API."""
    url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    payload = {
        "number": number,
        "text": text,
    }
    resp = httpx.post(url, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()

def send_document(number: str, file_path: str, filename: str, caption: str = "") -> dict:
    """Sends a document (e.g. resume PDF) as base64 to a WhatsApp number via Evolution API."""
    url = f"{EVOLUTION_API_URL}/message/sendMedia/{EVOLUTION_INSTANCE}"
    with open(file_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "number": number,
        "mediatype": "document",
        "mimetype": "application/pdf",
        "media": encoded,
        "fileName": filename,
        "caption": caption,
    }
    resp = httpx.post(url, headers=HEADERS, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()