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
DISCOVERY_CSV_PATH = os.getenv("DISCOVERY_CSV_PATH")

APPLICANT_NAME = os.getenv("APPLICANT_NAME")
APPLICANT_EMAIL = os.getenv("APPLICANT_EMAIL")
APPLICANT_PHONE = os.getenv("APPLICANT_PHONE")
APPLICANT_ADDRESS = os.getenv("APPLICANT_ADDRESS")
APPLICANT_BIRTH_DATE = os.getenv("APPLICANT_BIRTH_DATE")
APPLICANT_EDUCATION = os.getenv("APPLICANT_EDUCATION")
APPLICANT_COURSE = os.getenv("APPLICANT_COURSE")
APPLICANT_CITY = os.getenv("APPLICANT_CITY")
APPLICANT_EXPERIENCE_LEVEL = os.getenv("APPLICANT_EXPERIENCE_LEVEL")

SLEEP_MIN, SLEEP_MAX = 3, 6
LONG_PAUSE_EVERY = 7
LONG_PAUSE_MIN, LONG_PAUSE_MAX = 10, 20
DRY_RUN = os.getenv("DRY_RUN").lower() in ("true", "1", "yes")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")

SKIP_DELAYS = os.getenv("SKIP_DELAYS").lower() in ("true", "1", "yes")

CONFIDENCE_CONFIRMED = int(os.getenv("CONFIDENCE_CONFIRMADA") or 80)
CONFIDENCE_UNSURE = int(os.getenv("CONFIDENCE_INCERTO") or 50)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_REVIEW_CHANNEL_ID = int(os.getenv("DISCORD_REVIEW_CHANNEL_ID"))


def validate_config():
    """Checks if the essential configurations are present before running the program"""
    missing = []
    if not EMAIL_USER:
        missing.append("EMAIL_USER")
    if not EMAIL_PASS:
        missing.append("EMAIL_PASS")
    if not RESUME_PATH or not os.path.exists(RESUME_PATH):
        missing.append(f"resume file ({RESUME_PATH})")
    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if not DB_PATH or not os.path.exists(DB_PATH):
        missing.append(f"database file ({DB_PATH})")

    if missing:
        raise RuntimeError("Missing config. Missing: " + ", ".join(missing))