import sqlite3

from database.db import register_application
from database.models import Applications
from mailer.templates import render_generic, render_with_job
from mailer.sender import build_email, send_email, save_log
from whatsapp.sender import send_whatsapp_application, save_whatsapp_log

def process_company(conn: sqlite3.Connection, company: str, email_dest: str,
                     recipients: list[str] = None,
                     has_job: bool = False, job_type: str = None,
                     job_title: str = None, job_url: str = None,
                     whatsapp_number: str = None):
    """email_dest is the company's unique identifier in the database.
    recipients is the complete list of addresses that should receive the email.
    has_job/job_type/job_title/job_url come directly from the manually filled CSV."""
    recipients = recipients or [email_dest]

    if has_job and job_title:
        print(f"  -> Job provided: {job_type or 'job'} - {job_title}")
        body = render_with_job(company, job_type, job_title, job_url)
    else:
        print("  -> No job provided. Using the generic template.")
        body = render_generic(company)

    application = Applications(
        company=company, email=email_dest,
        job_type=job_type if has_job else None,
        job_title=job_title if has_job else None,
        job_url=job_url if has_job else None,
    )

    msg = build_email(recipients, body)
    try:
        send_email(msg, recipients)
        save_log(company, body)
        application.status = "Sent"
        print(f"  [OK] Email sent to {company}")
    except Exception as e:
        application.status = "Error"
        application.observations = f"Email: {e}"
        print(f"  [ERROR] Email failed: {e}")

    if whatsapp_number:
        try:
            send_whatsapp_application(whatsapp_number, body)
            save_whatsapp_log(company, body)
            application.whatsapp_status = "Sent"
            print(f"  [OK] WhatsApp sent to {company}")
        except Exception as e:
            application.whatsapp_status = "Error"
            prev = application.observations or ""
            application.observations = (prev + f" | WhatsApp: {e}").strip(" |")
            print(f"  [ERROR] WhatsApp failed: {e}")

    register_application(conn, application)