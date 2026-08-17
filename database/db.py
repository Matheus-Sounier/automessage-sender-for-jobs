import sqlite3
from datetime import datetime
from typing import Optional
from core.config import DB_PATH
from database.models import Applications


def ensure_schema(conn: sqlite3.Connection):
    cur = conn.execute("PRAGMA table_info(applications)")
    columns = [row[1] for row in cur.fetchall()]
    if "form_status" not in columns:
        conn.execute("ALTER TABLE applications ADD COLUMN form_status TEXT")
        conn.commit()


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            career_url TEXT NOT NULL UNIQUE,
            email TEXT,
            whatsapp TEXT,
            whatsapp_status TEXT DEFAULT 'Not informed',
            status TEXT DEFAULT 'Not sent',
            route TEXT,
            llm_confidence INTEGER,
            job_type TEXT,
            job_title TEXT,
            job_url TEXT,
            message_preview TEXT,
            date_sent TEXT,
            response TEXT,
            observations TEXT,
            form_status TEXT
        )
    """)
    conn.commit()
    ensure_schema(conn)
    return conn


def already_sent(conn: sqlite3.Connection, email: str) -> bool:
    cur = conn.execute("SELECT status FROM applications WHERE email = ?", (email,))
    row = cur.fetchone()
    return row is not None and row[0] == "Sent"


def already_scanned(conn: sqlite3.Connection, career_url: str) -> bool:
    """Return True if URL was already processed."""
    cur = conn.execute("SELECT id FROM applications WHERE career_url = ?", (career_url,))
    return cur.fetchone() is not None


def register_application(conn: sqlite3.Connection, application: Applications):
    application.date_sent = application.date_sent or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO applications (
            company, career_url, email, whatsapp, whatsapp_status, status,
            route, llm_confidence, job_type, job_title, job_url,
            message_preview, date_sent, response, observations, form_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(career_url) DO UPDATE SET
            email=excluded.email,
            whatsapp=excluded.whatsapp,
            whatsapp_status=excluded.whatsapp_status,
            status=excluded.status,
            route=excluded.route,
            llm_confidence=excluded.llm_confidence,
            job_type=excluded.job_type,
            job_title=excluded.job_title,
            job_url=excluded.job_url,
            message_preview=excluded.message_preview,
            date_sent=excluded.date_sent,
            response=COALESCE(excluded.response, response),
            observations=COALESCE(excluded.observations, observations),
            form_status=COALESCE(excluded.form_status, form_status)
    """, (application.company, application.career_url, application.email,
          application.whatsapp, application.whatsapp_status, application.status,
          application.route, application.llm_confidence, application.job_type,
          application.job_title, application.job_url, application.message_preview,
          application.date_sent, application.response, application.observations,
          application.form_status))
    conn.commit()


def get_pending_review(conn: sqlite3.Connection) -> list[Applications]:
    """Return scanned applications pending review."""
    cur = conn.execute("""
        SELECT company, career_url, email, whatsapp, whatsapp_status, status,
               route, llm_confidence, job_type, job_title, job_url,
               message_preview, date_sent, response, observations, form_status
        FROM applications
        WHERE status = 'Not sent'
          AND route IN ('job_confirmed', 'uncertain')
        ORDER BY llm_confidence DESC
    """)
    rows = cur.fetchall()
    return [
        Applications(
            company=r[0], career_url=r[1], email=r[2], whatsapp=r[3],
            whatsapp_status=r[4], status=r[5], route=r[6], llm_confidence=r[7],
            job_type=r[8], job_title=r[9], job_url=r[10], message_preview=r[11],
            date_sent=r[12], response=r[13], observations=r[14], form_status=r[15],
        )
        for r in rows
    ]


def get_pending_forms(conn: sqlite3.Connection) -> list[Applications]:
    """Return applications with approved forms pending local fill."""
    cur = conn.execute("""
        SELECT company, career_url, email, whatsapp, whatsapp_status, status,
               route, llm_confidence, job_type, job_title, job_url,
               message_preview, date_sent, response, observations, form_status
        FROM applications
        WHERE form_status = 'approved'
          AND status != 'Rejected'
        ORDER BY company
    """)
    return [
        Applications(
            company=r[0], career_url=r[1], email=r[2], whatsapp=r[3],
            whatsapp_status=r[4], status=r[5], route=r[6], llm_confidence=r[7],
            job_type=r[8], job_title=r[9], job_url=r[10], message_preview=r[11],
            date_sent=r[12], response=r[13], observations=r[14], form_status=r[15],
        )
        for r in cur.fetchall()
    ]



def mark_form_approved(conn: sqlite3.Connection, career_url: str):
    conn.execute(
        "UPDATE applications SET form_status = 'approved' WHERE career_url = ?",
        (career_url,),
    )
    conn.commit()


def mark_form_submitted(conn: sqlite3.Connection, career_url: str):
    conn.execute(
        "UPDATE applications SET form_status = 'submitted' WHERE career_url = ?",
        (career_url,),
    )
    conn.commit()


def mark_form_failed(conn: sqlite3.Connection, career_url: str, reason: Optional[str] = None):
    if reason:
        conn.execute(
            "UPDATE applications SET form_status = 'failed', observations = ? WHERE career_url = ?",
            (reason, career_url),
        )
    else:
        conn.execute(
            "UPDATE applications SET form_status = 'failed' WHERE career_url = ?",
            (career_url,),
        )
    conn.commit()


def mark_status(conn: sqlite3.Connection, career_url: str, status: str):
    conn.execute(
        "UPDATE applications SET status = ? WHERE career_url = ?",
        (status, career_url),
    )
    conn.commit()