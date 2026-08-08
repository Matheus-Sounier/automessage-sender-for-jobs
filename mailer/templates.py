from core.constants import GENERIC_TEMPLATE, JOB_TEMPLATE, VALID_JOB_TYPES

def render_generic(company: str) -> str:
    return GENERIC_TEMPLATE.format(empresa=company)

def render_with_job(company: str, job_type: str, job_title: str, job_url: str) -> str:
    tipo_normalizado = (job_type or "").strip().lower()
    if tipo_normalizado not in VALID_JOB_TYPES:
        tipo_normalizado = "vaga"

    return JOB_TEMPLATE.format(
        empresa=company,
        tipo_vaga=tipo_normalizado,
        vaga_titulo=job_title,
        vaga_url=job_url or "",
    )