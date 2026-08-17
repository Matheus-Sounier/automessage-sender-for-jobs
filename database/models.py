from dataclasses import dataclass
from typing import Optional


@dataclass
class Applications:
    company: str
    career_url: str
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    whatsapp_status: Optional[str] = "Not informed"
    status: str = "Not sent"
    route: Optional[str] = None
    llm_confidence: Optional[int] = None
    job_type: Optional[str] = None
    job_title: Optional[str] = None
    job_url: Optional[str] = None
    message_preview: Optional[str] = None
    date_sent: Optional[str] = None
    response: Optional[str] = None
    observations: Optional[str] = None
    form_status: Optional[str] = None