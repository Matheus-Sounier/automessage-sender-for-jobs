import os
from datetime import datetime

from core.config import RESUME_PATH, LOGS_DIR, DRY_RUN
from core.utils import slug
from whatsapp.client import send_text, send_document

def send_whatsapp_application(number: str, text: str):
    """Sends the application message + resume PDF to a WhatsApp number."""
    if DRY_RUN:
        print(f"  [DRY_RUN] Simulating WhatsApp delivery to: {number}")
        return

    send_text(number, text)
    send_document(number, RESUME_PATH, "Curriculo.pdf", caption="Segue meu currículo em anexo.")

def save_whatsapp_log(company: str, text: str):
    folder = os.path.join(LOGS_DIR, datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{slug(company)}_whatsapp.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)