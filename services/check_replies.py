import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import sqlite3
from datetime import datetime

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.config import EMAIL_USER, EMAIL_PASS, IMAP_SERVER, DB_PATH

PUBLIC_DOMAINS = {
    "gmail.com", "gmail.com.br", "hotmail.com", "outlook.com", "outlook.com.br",
    "yahoo.com.br", "live.com", "uol.com.br", "bol.com.br",
    "ig.com.br", "terra.com.br", "icloud.com", "proton.me", "protonmail.com"
}

def get_sent_applications(conn: sqlite3.Connection) -> list[tuple[int, str, str, str]]:
    """Return sent applications that have not received a reply yet."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, company, email, date_sent FROM applications WHERE status = 'Sent' AND response IS NULL"
    )
    return cursor.fetchall()

def update_application_response(conn: sqlite3.Connection, app_id: int, response_text: str):
    """Store the received reply in the database."""
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE applications
        SET status = 'Replied', response = ?, observations = ?
        WHERE id = ?
        """,
        (response_text, f"Reply detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", app_id)
    )
    conn.commit()

def check_for_replies():
    conn = sqlite3.connect(DB_PATH)
    applications = get_sent_applications(conn)
    
    if not applications:
        print("None of the sent applications have received a reply yet")
        conn.close()
        return

    print(f"Checking replies for {len(applications)} companies...")

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")  # Select the inbox.
    except Exception as e:
        print(f"Error connecting to email: {e}")
        conn.close()
        return

    for app_id, company, email_address, date_sent in applications:
        date_sent_dt = None
        if date_sent:
            try:
                date_sent_dt = datetime.strptime(date_sent, "%Y-%m-%d %H:%M:%S")
            except Exception as e:
                print(f"  [!] Error parsing date_sent '{date_sent}': {e}")

        domain = email_address.split("@")[-1].lower() if "@" in email_address else ""
        
        if not domain or domain in PUBLIC_DOMAINS:
            search_criterion = f'(FROM "{email_address}")'
            search_type = "exact email"
        else:
            search_criterion = f'(FROM "{domain}")'
            search_type = f"domain ({domain})"
            
        print(f"Searching replies for {company} using {search_type}...")
        status, messages = mail.search(None, search_criterion)
        
        if status == "OK" and messages[0]:
            mail_ids = messages[0].split()
            
            latest_email_id = mail_ids[-1]
            status, data = mail.fetch(latest_email_id, "(RFC822)")
            
            if status == "OK":
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                if date_sent_dt:
                    email_date_str = msg.get("Date")
                    if email_date_str:
                        try:
                            email_date = parsedate_to_datetime(email_date_str)
                            email_date_local = email_date.astimezone().replace(tzinfo=None)
                            if email_date_local <= date_sent_dt:
                                print(f"  [-] The latest email from {company} is old ({email_date_local}). Application sent at: {date_sent_dt}. Ignoring.")
                                continue
                        except Exception as e:
                            print(f"  [!] Could not verify the email date: {e}")

                print(f"  [!] Reply found from: {company} ({email_address})")
                
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8", errors="ignore")
                
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="ignore")
                
                # Create a short reply summary
                snippet = f"Subject: {subject}\n\n{body[:300]}..."
                
                # Update the database
                update_application_response(conn, app_id, snippet)
                print(f"  [OK] Database updated for {company}.")
        else:
            print(f"  [-] No reply from {company} ({email_address}) yet.")

    # Close 
    mail.close()
    mail.logout()
    conn.close()


if __name__ == "__main__":
    check_for_replies()