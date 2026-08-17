import httpx
import json

from core.config import OPENROUTER_API_KEY, OPENROUTER_MODEL

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def classify_job_presence(clean_text: str, signals: dict) -> dict:
    prompt = f"""Analise o texto de um site institucional e determine se há vaga de emprego em TI.
Sinais já detectados: {signals}
Texto do site:
{(clean_text or "")[:3000]}

Responda em JSON com exatamente estes campos:
{{
  "has_job": bool,
  "confidence": 0-100,
  "reason": "...",
  "job_title": "..." ou null,
  "job_type": "estágio" | "trainee" | "júnior" | "aprendiz de ti" | null
}}
Use job_type=null se não for possível identificar o tipo com clareza."""

    try:
        resp = httpx.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            },
            timeout=30,
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"OpenRouter HTTP error {exc.response.status_code}: {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"OpenRouter request error: {exc}") from exc

    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    except Exception as exc:
        raise RuntimeError(
            f"OpenRouter returned unexpected response format: {exc}. Raw body: {resp.text}"
        ) from exc

    def _extract_json_text(s: str) -> str:
        if not s:
            return s
        s = s.strip()
        if s.startswith("```") and s.endswith("```"):
            parts = s.split("\n")
            if len(parts) >= 3:
                return "\n".join(parts[1:-1]).strip()
            else:
                s = "\n".join(parts[1:]).strip()
        import re
        m = re.search(r"\{[\s\S]*\}", s)
        if m:
            return m.group(0)
        return s

    cleaned = _extract_json_text(content)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"OpenRouter returned invalid JSON: {exc}. Content: {content}"
        ) from exc