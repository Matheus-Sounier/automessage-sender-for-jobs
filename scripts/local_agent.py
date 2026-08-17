import argparse
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.config import (
    APPLICANT_ADDRESS,
    APPLICANT_BIRTH_DATE,
    APPLICANT_COURSE,
    APPLICANT_EDUCATION,
    APPLICANT_EMAIL,
    APPLICANT_EXPERIENCE_LEVEL,
    APPLICANT_NAME,
    APPLICANT_PHONE,
    APPLICANT_CITY,
    RESUME_PATH,
)
from database.db import get_pending_forms, init_db, mark_form_submitted, mark_status
from discovery.form_filler import fill_generic_form, has_resume_upload_field
from mailer.templates import build_message

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Local agent que preenche formulários aprovados e marca o envio no banco de dados."
    )
    parser.add_argument("--company", help="Processa somente esta empresa")
    parser.add_argument("--url", help="Processa somente esta URL")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Executa apenas uma vez e encerra.",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=60,
        help="Intervalo em segundos entre verificações de formulários pendentes.",
    )
    parser.add_argument("--name", default=APPLICANT_NAME)
    parser.add_argument("--email", default=APPLICANT_EMAIL)
    parser.add_argument("--phone", default=APPLICANT_PHONE)
    parser.add_argument("--resume", default=RESUME_PATH)
    parser.add_argument("--message", help="Mensagem manual; por padrão usa o template da candidatura")
    parser.add_argument("--address", default=APPLICANT_ADDRESS)
    parser.add_argument("--birth-date", default=APPLICANT_BIRTH_DATE)
    parser.add_argument("--education", default=APPLICANT_EDUCATION)
    parser.add_argument("--course", default=APPLICANT_COURSE)
    parser.add_argument("--city", default=APPLICANT_CITY)
    parser.add_argument("--experience-level", default=APPLICANT_EXPERIENCE_LEVEL)
    return parser.parse_args()

def process_pending_forms(conn, args: argparse.Namespace):
    pending = get_pending_forms(conn)

    if args.company:
        pending = [app for app in pending if app.company == args.company]
    if args.url:
        pending = [app for app in pending if app.career_url == args.url]

    if not pending:
        print("Nenhum formulário pendente encontrado.")
        return

    print(f"{len(pending)} formulário(s) pendente(s).")
    for app in pending:
        print(f"\n[local_agent] {app.company}: {app.career_url}")
        if not has_resume_upload_field(app.career_url):
            print(f"[local_agent] nenhum campo de upload de currículo encontrado em {app.career_url}; pulando.")
            continue

        result = fill_generic_form(
            url=app.career_url,
            name=args.name,
            email=args.email,
            phone=args.phone,
            resume_path=args.resume,
            message=args.message or build_message(app),
            address=args.address,
            birth_date=args.birth_date,
            education=args.education,
            course=args.course,
            city=args.city,
            experience_level=args.experience_level,
        )

        required_fields = ("name", "email", "phone", "file")
        if all(result[field] for field in required_fields):
            mark_form_submitted(conn, app.career_url)
            if app.status in ("No Contact Method", "Not sent", None):
                mark_status(conn, app.career_url, "Sent via form")
            print(f"[local_agent] formulário enviado e marcado como submitted: {app.career_url}")
        else:
            print(
                f"[local_agent] formulário não foi marcado como concluído. Campos obrigatórios faltando: {', '.join([k for k in required_fields if not result[k]])}"
            )

def main():
    args = parse_args()
    conn = init_db()
    try:
        while True:
            process_pending_forms(conn, args)
            if args.once:
                break
            print(f"Aguardando {args.poll_interval}s para nova verificação...")
            time.sleep(args.poll_interval)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
