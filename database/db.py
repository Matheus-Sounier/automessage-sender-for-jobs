import sqlite3
from datetime import datetime

from core.config import DB_PATH
from database.models import Applications

def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            whatsapp_status TEXT DEFAULT 'Not informed',
            status TEXT DEFAULT 'Not sent',
            job_type TEXT,
            job_title TEXT,
            job_url TEXT,
            date_sent TEXT,
            response TEXT,
            observations TEXT
        )
    """)
    conn.commit()
    return conn

def already_sent(conn: sqlite3.Connection, email: str) -> bool:
    cur = conn.execute("SELECT status FROM applications WHERE email = ?", (email,))
    row = cur.fetchone()
    return row is not None and row[0] == "Sent"

def register_application(conn: sqlite3.Connection, application: Applications):
    application.date_sent = application.date_sent or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO applications (company, email, whatsapp_status, status, job_type, job_title, job_url, date_sent, observations)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET
            whatsapp_status=excluded.whatsapp_status,
            status=excluded.status,
            job_type=excluded.job_type,
            job_title=excluded.job_title,
            job_url=excluded.job_url,
            date_sent=excluded.date_sent,
            observations=excluded.observations
    """, (application.company, application.email, application.whatsapp_status, application.status,
          application.job_type, application.job_title, application.job_url,
            application.date_sent, application.observations))
    conn.commit()