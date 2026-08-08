import csv
import time
import random
import argparse

from core import config
from database.db import init_db, already_sent
from services.apply import process_company
from services.check_replies import check_for_replies
from core.utils import normalize_br_number

def main():
    parser = argparse.ArgumentParser(description="Application and reply manager.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check for replies in the inbox from companies contacted.",
    )
    args = parser.parse_args()

    config.validate_config()
    conn = init_db()

    if args.check:
        print("Starting reply check...")
        check_for_replies()
        conn.close()
        return

    with open(config.CSV_PATH, newline="", encoding="utf-8") as f:
        companies = list(csv.DictReader(f))

    for i, row in enumerate(companies, start=1):
        company = row["company_name"].strip()
        email_dest = row["primary_email"].strip()
        optional_email = (row.get("optional_email") or "").strip()
        whatsapp_raw = (row.get("optional_whatsapp") or "").strip()
        whatsapp_number = normalize_br_number(whatsapp_raw) if whatsapp_raw else None
        has_job = (row.get("has_job") or "").strip().lower() in ("yes", "true", "1")
        job_type = (row.get("job_type") or "").strip() or None
        job_title = (row.get("job_title") or "").strip() or None
        job_url = (row.get("job_url") or "").strip() or None

        recipients = [email_dest] + ([optional_email] if optional_email else [])

        if already_sent(conn, email_dest):
            print(f"[SKIP] Already sent to {company}")
            continue

        print(f"[{i}/{len(companies)}] {company}")
        process_company(conn, company, email_dest, recipients, whatsapp_number=whatsapp_number,
                         has_job=has_job, job_type=job_type, job_title=job_title, job_url=job_url)

        if i % config.LONG_PAUSE_EVERY == 0:
            wait_time = random.uniform(config.LONG_PAUSE_MIN, config.LONG_PAUSE_MAX)
            print(f"  Long pause of {wait_time/60:.1f} min...")
        else:
            wait_time = random.uniform(config.SLEEP_MIN, config.SLEEP_MAX)
        time.sleep(wait_time)

    conn.close()

if __name__ == "__main__":
    main()