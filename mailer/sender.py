import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from core.config import EMAIL_USER, EMAIL_PASS, SMTP_SERVER, SMTP_PORT, RESUME_PATH, LOGS_DIR, DRY_RUN
from core.utils import slug

def build_email(recipients: list[str], body: str) -> MIMEMultipart:
    """recipients: list with 1 or more emails (e.g., [primary_email, optional_email])."""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = "Candidatura - Desenvolvedor Backend"
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with open(RESUME_PATH, "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="pdf")
        attachment.add_header("Content-Disposition", "attachment", filename="Curriculo.pdf")
        msg.attach(attachment)
    return msg

def send_email(msg: MIMEMultipart, recipients: list[str]):
    if DRY_RUN:
        print(f"  [DRY_RUN] Simulating email delivery to: {recipients}")
        return
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, recipients, msg.as_string())

def save_log(company: str, body: str):
    folder = os.path.join(LOGS_DIR, datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{slug(company)}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(body)