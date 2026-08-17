from core.constants import CAREER_URL_HINTS, CAREER_TEXT_HINTS, ATS_DOMAINS

def deterministic_signal(url: str, raw_html: str, clean_text: str) -> dict:
    """Deterministic signals (no LLM)."""
    clean_text = clean_text or ""
    return {
        "url_hit": any(h in url.lower() for h in CAREER_URL_HINTS),
        "text_hit": any(h in clean_text.lower() for h in CAREER_TEXT_HINTS),
        "ats_hit": any(d in raw_html.lower() for d in ATS_DOMAINS),
    }
def has_application_form(raw_html: str) -> bool:
    """Return True if HTML shows file upload and resume terms."""
    if not raw_html:
        return False
    lower = raw_html.lower()
    has_upload = 'type="file"' in lower or "type='file'" in lower
    resume_terms = ("currículo", "curriculo", "resume", "cv")
    return has_upload and any(term in lower for term in resume_terms)