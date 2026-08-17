import argparse
import os
import sys
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
from discovery.contact import extract_email, extract_phone
from discovery.fetch import fetch_and_clean
from discovery.form_filler import fill_generic_form, has_resume_upload_field
from discovery.signals import has_application_form


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Testa o preenchimento de formulário de candidatura e validação de contato na página."
    )
    parser.add_argument("--url", required=True, help="URL exata da página a testar")
    parser.add_argument("--name", default=APPLICANT_NAME)
    parser.add_argument("--email", default=APPLICANT_EMAIL)
    parser.add_argument("--phone", default=APPLICANT_PHONE)
    parser.add_argument(
        "--resume",
        default=RESUME_PATH,
        help="Caminho para o currículo a ser enviado",
    )
    parser.add_argument("--message", default=None)
    parser.add_argument("--address", default=APPLICANT_ADDRESS)
    parser.add_argument("--birth-date", default=APPLICANT_BIRTH_DATE)
    parser.add_argument("--education", default=APPLICANT_EDUCATION)
    parser.add_argument("--course", default=APPLICANT_COURSE)
    parser.add_argument("--city", default=APPLICANT_CITY)
    parser.add_argument("--experience-level", default=APPLICANT_EXPERIENCE_LEVEL)
    return parser.parse_args()

def print_contact_and_form_info(url: str):
    raw_html, clean_text = fetch_and_clean(url)
    if raw_html is None:
        raise RuntimeError("Não foi possível acessar a URL.")

    email = extract_email(clean_text or "", raw_html)
    phone = extract_phone(clean_text or "", raw_html)
    form_found = has_application_form(raw_html)

    print(f"URL testada: {url}")
    print(f"Email encontrado na página: {email}")
    print(f"WhatsApp/telefone encontrado na página: {phone}")
    print(f"Formulário detectado no HTML inicial: {form_found}")

    if not form_found:
        print("Verificando também o formulário renderizado no navegador...")
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)
            form_count = page.locator("form").count()
            file_count = page.locator('input[type="file"]').count()
            browser.close()

        print(f"Formulário renderizado detectado: {form_count > 0}")
        print(f"Campos de upload de arquivo renderizados: {file_count}")

def test_form(args: argparse.Namespace):
    missing = [
        option
        for option, value in (
            ("--name", args.name),
            ("--email", args.email),
            ("--phone", args.phone),
            ("--resume", args.resume),
        )
        if not value
    ]
    if missing:
        raise SystemExit("Para testar o formulário, informe: " + ", ".join(missing))
    if not os.path.isfile(args.resume):
        raise SystemExit(f"Currículo não encontrado: {args.resume}")

    if not has_resume_upload_field(args.url):
        print("Nenhum campo de upload de currículo encontrado; teste de formulário interrompido.")
        return

    print_contact_and_form_info(args.url)
    result = fill_generic_form(
        url=args.url,
        name=args.name,
        email=args.email,
        phone=args.phone,
        resume_path=args.resume,
        message=args.message,
        address=args.address,
        birth_date=args.birth_date,
        education=args.education,
        course=args.course,
        city=args.city,
        experience_level=args.experience_level,
    )
    print("Resultado do preenchimento:", result)
    print("Nenhum envio automático foi executado.")

def main():
    args = parse_args()
    test_form(args)

if __name__ == "__main__":
    main()
