import argparse
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Testa apenas a inspeção da página: sinaliza contatos, link de carreira e formulário."
    )
    parser.add_argument("--url", required=True, help="URL exata da página a testar")
    parser.add_argument(
        "--inspect",
        action="store_true",
        required=True,
        help="Verifica o conteúdo da página para contatos e formulário",
    )
    return parser.parse_args()

def inspect_url(url: str):
    from discovery.contact import extract_email, extract_phone
    from discovery.crawl import find_career_link
    from discovery.fetch import fetch_and_clean
    from discovery.signals import deterministic_signal, has_application_form

    raw_html, clean_text = fetch_and_clean(url)
    if raw_html is None:
        raise RuntimeError("Não foi possível acessar a URL.")

    print(f"URL testada: {url}")
    print(f"HTML recebido: {len(raw_html)} caracteres")
    print(f"Texto extraído: {len(clean_text or '')} caracteres")
    print("Sinais:", deterministic_signal(url, raw_html, clean_text or ""))
    print("Email:", extract_email(clean_text or "", raw_html))
    print("WhatsApp/telefone:", extract_phone(clean_text or "", raw_html))
    static_form = has_application_form(raw_html)
    print("Formulário de candidatura no HTML inicial:", static_form)
    if not static_form:
        print("Verificando também o formulário renderizado no navegador...")
        rendered = inspect_rendered_form(url)
        print("Formulário de candidatura detectado no DOM renderizado:", rendered["detected"])
        print(
            "Elementos renderizados (diagnóstico):",
            f'{rendered["forms"]} formulário(s) HTML genérico(s), '
            f'{rendered["files"]} campo(s) de upload de currículo, '
            f'{rendered["inputs"]} input(s), '
            f'{rendered["textareas"]} textarea(s)',
        )
    print("Link de carreira encontrado:", find_career_link(url, raw_html))

def inspect_rendered_form(url: str) -> dict[str, int | bool]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        form_count = page.locator("form").count()
        file_count = page.locator('input[type="file"]').count()
        input_count = page.locator("input").count()
        textarea_count = page.locator("textarea").count()
        browser.close()
    return {
        "detected": file_count > 0,
        "forms": form_count,
        "files": file_count,
        "inputs": input_count,
        "textareas": textarea_count,
    }

def main():
    args = parse_args()
    inspect_url(args.url)

if __name__ == "__main__":
    main()