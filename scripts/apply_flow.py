import csv
import random
import sys
import time
from pathlib import Path

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if sys.path[0] == str(script_dir):
    sys.path.pop(0)
sys.path.insert(0, str(project_root))

from discord_bot.client import client
from discord_bot.approval import ask_approval
from core import config
from core.config import (
    DISCOVERY_CSV_PATH,
    LONG_PAUSE_EVERY,
    LONG_PAUSE_MAX,
    LONG_PAUSE_MIN,
    SLEEP_MAX,
    SLEEP_MIN,
)
from database.db import init_db, get_pending_review, mark_form_approved, mark_status
from discovery.classify import classify_job_presence
from discovery.contact import extract_email, extract_phone
from discovery.crawl import find_career_link
from discovery.fetch import fetch_and_clean
from discovery.fetch import start_shared_browser, stop_shared_browser, _use_shared_browser
from discovery.router import route
from discovery.signals import deterministic_signal, has_application_form
from mailer.templates import build_message
from mailer.sender import build_email, send_email, save_log
from whatsapp.sender import send_whatsapp_application, save_whatsapp_log
from playwright.sync_api import sync_playwright

def load_companies(discovery_csv_path: str = DISCOVERY_CSV_PATH) -> list[dict]:
    with open(discovery_csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def process_company(conn, company: str, career_url: str):
    if not career_url:
        raise ValueError(f"career_url is required for discovery (company: {company})")

    from database.db import already_scanned, register_application
    from database.models import Applications

    if already_scanned(conn, career_url):
        return None

    raw_html, clean_text = fetch_and_clean(career_url)
    if raw_html is None:
        return None

    try:
        print(f"Tested URL: {career_url}")
        print(f"HTML length: {len(raw_html)}")
        print(f"Extracted text length: {len(clean_text or '')}")
        print("Signals:", deterministic_signal(career_url, raw_html, clean_text or ""))
        print("Email:", extract_email(clean_text or "", raw_html))
        print("WhatsApp/phone:", extract_phone(clean_text or "", raw_html))
        static_form = has_application_form(raw_html)
        print("Initial HTML application form:", static_form)
        if not static_form:
            print("Also checking rendered DOM for application form...")
            try:
                shared = _use_shared_browser()
                if shared is not None:
                    page = shared.new_page()
                    page.goto(career_url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(1500)
                    form_count = page.locator("form").count()
                    file_count = page.locator('input[type="file"]').count()
                    input_count = page.locator("input").count()
                    textarea_count = page.locator("textarea").count()
                    page.close()
                    detected = file_count > 0
                else:
                    with sync_playwright() as playwright:
                        browser = playwright.chromium.launch(headless=True)
                        page = browser.new_page()
                        page.goto(career_url, wait_until="domcontentloaded", timeout=30000)
                        page.wait_for_timeout(2000)
                        form_count = page.locator("form").count()
                        file_count = page.locator('input[type="file"]').count()
                        input_count = page.locator("input").count()
                        textarea_count = page.locator("textarea").count()
                        browser.close()
                    detected = file_count > 0
            except Exception:
                detected = False
                form_count = file_count = input_count = textarea_count = 0

            print("Application form detected in rendered DOM:", detected)
            print(
                "Rendered elements (diagnostic):",
                f"{form_count} generic HTML form(s), {file_count} file upload field(s), {input_count} input(s), {textarea_count} textarea(s)",
            )
        print("Career link found:", find_career_link(career_url, raw_html))
    except Exception as e:
        print(f"[discover] failed to print inspection diagnostic for {career_url}: {e}")

    if not clean_text or len(clean_text) < 100:
        fallback_url = find_career_link(career_url, raw_html)
        if fallback_url:
            raw_html, clean_text = fetch_and_clean(fallback_url)
            career_url = fallback_url

    if raw_html is None:
        return None

    signals = deterministic_signal(career_url, raw_html, clean_text)
    try:
        llm_result = classify_job_presence(clean_text, signals)
    except Exception as e:
        print(f"[discover] erro LLM {career_url}: {e}")
        return None

    company_route = route(signals, llm_result)
    contact_email = extract_email(clean_text, raw_html)
    contact_phone = extract_phone(clean_text, raw_html)
    form_available = has_application_form(raw_html)

    if not contact_email and not contact_phone:
        print(f"[discover] pulando {company} — sem email nem whatsapp detectados.")
        return None

    application = Applications(
        company=company,
        career_url=career_url,
        email=contact_email,
        whatsapp=contact_phone,
        route=company_route,
        llm_confidence=llm_result.get("confidence"),
        job_type=llm_result.get("job_type"),
        job_title=llm_result.get("job_title"),
        job_url=career_url if llm_result.get("has_job") else None,
        status="Not sent",
        observations="form_available" if form_available else None,
        form_status="pending" if form_available else None,
    )
    register_application(conn, application)
    return application

def run_discovery():
    conn = init_db()
    companies = load_companies()

    try:
        start_shared_browser(headless=True)
    except Exception:
        pass

    results = {"job_confirmed": 0, "uncertain": 0, "spontaneous": 0, "skipped": 0}

    for i, row in enumerate(companies, start=1):
        company = row["company"]
        url = row["career_url"]

        discovery = process_company(conn, company, url)
        if discovery is None:
            results["skipped"] += 1
            print()
            continue

        results[discovery.route] += 1
        print()

        if not config.SKIP_DELAYS:
            time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
        if i % LONG_PAUSE_EVERY == 0:
            pause = random.uniform(LONG_PAUSE_MIN, LONG_PAUSE_MAX)
            print(f"[discover] long pause {pause:.0f}s after {i} companies")
            if not config.SKIP_DELAYS:
                time.sleep(pause)

    conn.close()
    try:
        stop_shared_browser()
    except Exception:
        pass
    print(f"[discover] finished: {results}")
    return results

@client.event
async def on_ready():
    print(f"Bot connected as {client.user}")
    print(f"Visible guilds: {[(g.name, g.id) for g in client.guilds]}")
    conn = init_db()

    try:
        print("Starting discovery and saving applications to DB...")
        results = run_discovery()
        print(f"Discovery finished: {results}")

        await review_and_send(conn)
    finally:
        conn.close()
        await client.close()

async def review_and_send(conn):
    pending = get_pending_review(conn)

    if not pending:
        print("No pending applications for review.")
        return

    for app in pending:
        message = build_message(app)

        approved = await ask_approval(
            app.company,
            app.route,
            app.llm_confidence,
            app.job_title,
            app.email,
            app.whatsapp,
            message,
            app.observations == "form_available",
        )

        if not approved:
            mark_status(conn, app.career_url, "Rejected")
            continue

        if app.observations == "form_available":
            mark_form_approved(conn, app.career_url)

        sent_via_something = False

        if app.email:
            msg = build_email([app.email], message)
            send_email(msg, [app.email])
            save_log(app.company, message)
            sent_via_something = True

        if app.whatsapp:
            send_whatsapp_application(app.whatsapp, message)
            save_whatsapp_log(app.company, message)
            sent_via_something = True

        mark_status(conn, app.career_url, "Sent" if sent_via_something else "No Contact Method")

if __name__ == "__main__":
    config.validate_config()
    client.run(config.DISCORD_BOT_TOKEN)