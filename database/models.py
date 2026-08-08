from dataclasses import dataclass
from typing import Optional

@dataclass
class Applications:
    company: str
    email: str
    whatsapp_status: Optional[str] = "Not informed"
    status: str = "Not sent"
    job_type: Optional[str] = None
    job_title: Optional[str] = None
    job_url: Optional[str] = None
    date_sent: Optional[str] = None
    response: Optional[str] = None
    observations: Optional[str] = None