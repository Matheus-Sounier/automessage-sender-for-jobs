import sqlite3

def get_status_summary(conn: sqlite3.Connection) -> dict:
    """Returns a count of applications by status (Sent, Error, Replied, etc.)."""
    cur = conn.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
    return dict(cur.fetchall())