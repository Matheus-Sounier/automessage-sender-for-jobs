import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
IMAP_SERVER = os.getenv("IMAP_SERVER")

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
AUTHENTICATION_API_KEY = os.getenv("AUTHENTICATION_API_KEY")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE")

RESUME_PATH = os.getenv("RESUME_PATH")
CSV_PATH = os.getenv("CSV_PATH")
DB_PATH = os.getenv("DB_PATH")
LOGS_DIR = os.getenv("LOGS_DIR")

SLEEP_MIN, SLEEP_MAX = 15, 30
LONG_PAUSE_EVERY = 10
LONG_PAUSE_MIN, LONG_PAUSE_MAX = 300, 600
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("true", "1", "yes")

def validate_config():
    """Checks if the essential configurations are present before running the program"""
    missing = []
    if not EMAIL_USER:
        missing.append("EMAIL_USER")
    if not EMAIL_PASS:
        missing.append("EMAIL_PASS")
    if not RESUME_PATH or not os.path.exists(RESUME_PATH):
        missing.append(f"resume file ({RESUME_PATH})")

    if missing:
        raise RuntimeError("Missing config. Missing: " + ", ".join(missing))