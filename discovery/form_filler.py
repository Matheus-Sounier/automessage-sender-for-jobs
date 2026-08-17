import re
import unicodedata
from playwright.sync_api import sync_playwright, Page

NAME_PATTERNS = [r"nome"]
EMAIL_PATTERNS = [r"e-?mail"]
PHONE_PATTERNS = [
    r"telefone",
    r"celular",
    r"número",
    r"numero",
    r"whatsapp",
    r"contato",
]
FILE_PATTERNS = [r"currículo", r"curriculo", r"arquivo", r"anexar"]
MESSAGE_PATTERNS = [
    r"mensagem",
    r"apresentação",
    r"apresentacao",
    r"carta de apresentação",
    r"carta de apresentacao",
    r"experiência",
    r"experiencia",
    r"experincia",
    r"habilidades",
    r"competências",
    r"competencias",
    r"interesses",
    r"qualificações",
    r"qualificacoes",
    r"conhecimentos",
    r"perfil",
    r"objetivo profissional",
    r"sobre você",
    r"sobre voce",
]
CITY_PATTERNS = [r"cidade", r"estado", r"localização", r"localizacao"]
EXPERIENCE_PATTERNS = [
    r"nível de experiência",
    r"nivel de experiencia",
    r"experiência profissional",
    r"experiencia profissional",
    r"senioridade",
]

FIELD_ALIASES = {
    "name": {"nome", "name", "full name"},
    "email": {"email", "e mail", "mail", "e-mail"},
    "phone": {"telefone", "celular", "whatsapp", "numero", "número", "contato", "mobile", "phone"},
    "address": {"endereco", "endereço", "address", "rua", "logradouro", "endereço residencial", "residencia", "residência"},
    "birth_date": {"data de nascimento", "nascimento", "birth date", "date of birth", "data nascimento"},
    "education": {"escolaridade", "grau de instrução", "grau de instrucao", "education", "formação", "formacao"},
    "course": {"curso", "course", "especialização", "especializacao", "degree", "programa"},
    "linkedin": {"linkedin", "linked in"},
    "resume": {"curriculo", "currículo", "cv", "resume", "curriculum", "arquivo", "anexar"},
    "city": {"cidade", "estado", "localizacao", "localização", "city"},
    "experience_level": {"nivel de experiencia", "nível de experiência", "experiencia profissional", "experiência profissional", "senioridade"},
    "message": {"mensagem", "apresentacao", "apresentação", "carta de apresentacao", "carta de apresentação", "perfil", "sobre voce", "sobre você", "habilidades", "competencias", "competências", "interesses", "experiencia", "experiência"},
}

EDUCATION_PRIORITY = [
    "graduando",
    "graduado",
    "gradua",
    "pós graduando",
    "pos graduando",
    "pós graduado",
    "pos graduado",
    "mestrando",
    "mestrado",
    "doutorando",
    "doutorado",
    "técnico",
    "tecnico",
]

EDUCATION_GRADUATION_TERMS = {
    "graduando",
    "graduado",
    "gradua",
    "graduacao",
    "graduação",
    "faculdade",
    "ensino superior",
    "bacharel",
    "licenciatura",
    "engenharia de software",
    "curso superior",
}

EDUCATION_TECHNICAL_TERMS = {
    "tecnico",
    "técnico",
    "tecnico em",
    "curso tecnico",
    "ensino tecnico",
    "tecnologo",
    "tecnóloga",
}

AREA_PRIORITY_KEYWORDS = [
    "tecnologia", "ti", "desenvolvimento", "dev", "software",
    "sistemas", "engenharia de software", "backend", "suporte técnico",
    "suporte", "infraestrutura", "redes",
]


def _normalize(value: str) -> str:
    if not value:
        return ""
    without_accents = unicodedata.normalize("NFD", value)
    without_accents = "".join(char for char in without_accents if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9\s]", " ", without_accents.lower()).strip()


def field_matches_text(label: str, field_name: str) -> bool:
    if not label:
        return False
    normalized_label = _normalize(label)
    aliases = FIELD_ALIASES.get(field_name, {field_name})

    for alias in aliases:
        alias_norm = _normalize(alias)
        if not alias_norm:
            continue
        if alias_norm in normalized_label:
            return True
        if re.search(rf"(?<![a-z0-9]){re.escape(alias_norm)}(?![a-z0-9])", normalized_label):
            return True
        alias_tokens = alias_norm.split()
        if len(alias_tokens) > 1 and all(token in normalized_label.split() for token in alias_tokens):
            return True
    return False


def _extract_field_metadata(locator) -> str:
    metadata_parts = [locator.get_attribute("name"), locator.get_attribute("id"), locator.get_attribute("placeholder"), locator.get_attribute("aria-label")]
    try:
        label_text = locator.evaluate(
            """
            (el) => {
                const texts = [];
                if (el.labels) {
                    texts.push(...Array.from(el.labels).map(label => label.textContent || ''));
                }
                if (el.id) {
                    const byFor = Array.from(document.querySelectorAll('label[for]')).filter(label => label.htmlFor === el.id).map(label => label.textContent || '');
                    texts.push(...byFor);
                }
                const parentLabel = el.closest('label');
                if (parentLabel) texts.push(parentLabel.textContent || '');
                const parent = el.parentElement;
                if (parent) texts.push(parent.textContent || '');
                const nearestGroup = el.closest('fieldset, div, li, span, section');
                if (nearestGroup && nearestGroup !== parent) texts.push(nearestGroup.textContent || '');
                return texts.join(' ');
            }
            """
        )
    except Exception:
        label_text = ""
    metadata_parts.append(label_text)
    return " ".join(part for part in metadata_parts if part and part.strip())


def _try_fill_by_label(page: Page, patterns: list[str], value: str) -> bool:
    for pattern in patterns:
        try:
            locator = page.get_by_label(re.compile(pattern, re.IGNORECASE))
            if locator.count() > 0:
                locator.first.fill(value)
                return True
        except Exception:
            continue
    return False


def _try_upload_by_label(page: Page, patterns: list[str], file_path: str) -> bool:
    for pattern in patterns:
        try:
            locator = page.get_by_label(re.compile(pattern, re.IGNORECASE))
            if locator.count() > 0:
                locator.first.set_input_files(file_path)
                return True
        except Exception:
            continue
    return False


def _try_fill_field(page: Page, field_name: str, value: str) -> bool:
    for index in range(page.locator("input, textarea, select").count()):
        try:
            candidate = page.locator("input, textarea, select").nth(index)
            if not candidate.is_visible():
                continue
            tag_type = candidate.get_attribute("type") or ""
            if tag_type.lower() in ("checkbox", "radio"):
                continue
            metadata = _extract_field_metadata(candidate)
            if not field_matches_text(metadata, field_name):
                continue

            tag_name = candidate.evaluate("element => element.tagName")
            if tag_name == "SELECT":
                options = candidate.locator("option").all_inner_texts()
                if options:
                    for option_text in options:
                        if _normalize(value) in _normalize(option_text):
                            candidate.select_option(label=option_text)
                            return True
                    candidate.select_option(label=options[0])
                    return True
                continue

            candidate.fill(value)
            return True
        except Exception:
            continue
    return False


def _try_upload_field(page: Page, field_name: str, file_path: str) -> bool:
    for index in range(page.locator("input[type='file']").count()):
        try:
            candidate = page.locator("input[type='file']").nth(index)
            if not candidate.is_visible():
                continue
            metadata = _extract_field_metadata(candidate)
            if field_matches_text(metadata, field_name):
                candidate.set_input_files(file_path)
                return True
        except Exception:
            continue
    return False


def has_resume_upload_field(url: str) -> bool:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        count = page.locator("input[type='file']").count()
        browser.close()
        return count > 0


def _try_fill_checkbox_or_radio(page: Page, field_name: str, preferred_terms: list[str], target_value: str | None = None) -> bool:
    inputs = page.locator("input[type='checkbox'], input[type='radio']")
    candidates = []
    for index in range(inputs.count()):
        try:
            candidate = inputs.nth(index)
            if not candidate.is_visible():
                continue

            metadata = _extract_field_metadata(candidate)
            value = (candidate.get_attribute("value") or "").strip()
            option_text = candidate.evaluate(
                """
                (el) => {
                    const labelEls = el.labels ? Array.from(el.labels) : [];
                    const labelText = labelEls.map(label => (label.textContent || '').trim()).filter(Boolean).join(' ');
                    const directLabel = el.closest('label');
                    const directText = directLabel ? (directLabel.textContent || '').trim() : '';
                    const textParts = [];
                    if (labelText) textParts.push(labelText);
                    if (directText && !textParts.includes(directText)) textParts.push(directText);
                    if (textParts.length) return textParts.join(' ');
                    const parent = el.parentElement;
                    if (parent) {
                        const parentText = (parent.textContent || '').trim();
                        if (parentText) return parentText;
                    }
                    return value || '';
                }
                """
            ) or ""

            text_for_matching = option_text or value or metadata
            if field_matches_text(metadata, field_name) or field_matches_text(text_for_matching, field_name) or field_matches_text(value, field_name):
                candidates.append((candidate, option_text, value, metadata))
        except Exception:
            continue

    if not candidates:
        return False

    target_norm = _normalize(target_value or "")
    ranked = []
    for candidate, option_text, value, metadata in candidates:
        option_norm = _normalize(option_text or value or metadata)
        score = 0

        if target_norm:
            if target_norm in option_norm:
                score += 300
            else:
                target_tokens = set(target_norm.split())
                option_tokens = set(option_norm.split())
                common = target_tokens & option_tokens
                if common:
                    score += 180

        for term in preferred_terms:
            term_norm = _normalize(term)
            if term_norm and term_norm in option_norm:
                score += 120

        if any(term in option_norm for term in ["graduando", "graduado", "gradua", "graduacao", "graduacao", "faculdade", "ensino superior", "bacharel", "licenciatura"]):
            score += 70
        if any(term in option_norm for term in ["tecnico", "tecnologo", "ensino tecnico", "curso tecnico"]):
            score += 60

        if target_norm and not target_norm in option_norm:
            score -= 200

        ranked.append((score, candidate))

    ranked.sort(key=lambda item: item[0], reverse=True)
    for _, candidate in ranked:
        try:
            candidate.check()
            return True
        except Exception:
            continue

    return False


def _try_fill_education(page: Page, education_value: str) -> bool:
    if not education_value:
        return False

    normalized = _normalize(education_value)
    if any(term in normalized for term in ["tecnico", "tecnologo", "ensino tecnico", "curso tecnico"]):
        preferred = [
            "tecnico",
            "técnico",
            "curso técnico",
            "ensino técnico",
            "tecnologo",
        ]
    else:
        preferred = [
            "graduando",
            "graduado",
            "gradua",
            "graduação",
            "graduacao",
            "faculdade",
            "ensino superior",
            "bacharel",
            "licenciatura",
        ]

    if _try_fill_checkbox_or_radio(page, "education", preferred, education_value):
        return True
    return _try_fill_field(page, "education", education_value)


def _try_fill_birth_date(page: Page, birth_date: str) -> bool:
    if not birth_date:
        return False
    return _try_fill_field(page, "birth_date", birth_date)


def _try_fill_message(page: Page, message: str) -> bool:
    for pattern in MESSAGE_PATTERNS:
        try:
            locator = page.get_by_label(re.compile(pattern, re.IGNORECASE))
            for index in range(locator.count()):
                candidate = locator.nth(index)
                if candidate.evaluate("element => element.tagName") == "TEXTAREA":
                    candidate.fill(message)
                    return candidate.input_value() == message
        except Exception:
            continue

    textareas = page.locator("textarea")
    for index in range(textareas.count()):
        textarea = textareas.nth(index)
        metadata = _extract_field_metadata(textarea)
        if field_matches_text(metadata, "message"):
            textarea.fill(message)
            return True

    if textareas.count() == 1:
        textareas.first.fill(message)
        return True
    return False


def _try_select_area(page: Page) -> str | None:
    """Procura um <select> perto de um label que fale de 'área', 'departamento', 'setor'.
    Escolhe a opção mais próxima do seu perfil (TI/dev/suporte)."""
    area_label_patterns = [r"área", r"area", r"departamento", r"setor", r"vaga\s+de\s+interesse"]

    for pattern in area_label_patterns:
        try:
            locator = page.get_by_label(re.compile(pattern, re.IGNORECASE))
            if locator.count() == 0:
                continue

            select_el = locator.first
            options = select_el.locator("option").all_inner_texts()

            normalized_options = {
                option_text: _normalize(option_text) for option_text in options
            }
            for keyword in AREA_PRIORITY_KEYWORDS:
                normalized_keyword = _normalize(keyword)
                for option_text in options:
                    if re.search(
                        rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)",
                        normalized_options[option_text],
                    ):
                        select_el.select_option(label=option_text)
                        return option_text

            print(f"[form] dropdown de área encontrado, mas nenhuma opção combina com TI. Opções disponíveis: {options}")
            return None
        except Exception:
            continue

    return None


def fill_generic_form(
    url: str,
    name: str,
    email: str,
    phone: str,
    resume_path: str,
    message: str | None = None,
    address: str | None = None,
    birth_date: str | None = None,
    education: str | None = None,
    course: str | None = None,
    city: str | None = None,
    experience_level: str | None = None,
) -> dict:
    result = {
        "name": False,
        "email": False,
        "phone": False,
        "address": False,
        "birth_date": False,
        "education": False,
        "course": False,
        "file": False,
        "area": None,
        "message": False,
        "city": False,
        "experience_level": False,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        result["name"] = _try_fill_field(page, "name", name) or _try_fill_by_label(page, NAME_PATTERNS, name)
        result["email"] = _try_fill_field(page, "email", email) or _try_fill_by_label(page, EMAIL_PATTERNS, email)
        result["phone"] = _try_fill_field(page, "phone", phone) or _try_fill_by_label(page, PHONE_PATTERNS, phone)
        result["address"] = _try_fill_field(page, "address", address) if address else False
        result["birth_date"] = _try_fill_birth_date(page, birth_date) if birth_date else False
        result["education"] = _try_fill_education(page, education or "graduando") if education else False
        result["course"] = _try_fill_field(page, "course", course) if course else False
        result["file"] = _try_upload_field(page, "resume", resume_path) or _try_upload_by_label(page, FILE_PATTERNS, resume_path)
        result["area"] = _try_select_area(page)
        if city:
            result["city"] = _try_fill_field(page, "city", city) or _try_fill_by_label(page, CITY_PATTERNS, city)
        if experience_level:
            result["experience_level"] = _try_fill_field(page, "experience_level", experience_level) or _try_fill_by_label(page, EXPERIENCE_PATTERNS, experience_level)
        if message:
            result["message"] = _try_fill_message(page, message) or _try_fill_field(page, "message", message)

        print(f"\nResultado do preenchimento: {result}")
        input("Pressione Enter DEPOIS de revisar (confira principalmente o campo de área)...")

        browser.close()

    return result