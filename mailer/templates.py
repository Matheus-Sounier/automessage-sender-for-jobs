from core.constants import GENERIC_TEMPLATE

def render_generic(company: str) -> str:
    return GENERIC_TEMPLATE.format(empresa=company)

def build_message(app) -> str:
    """Always use the generic template for sending messages."""
    return render_generic(app.company)