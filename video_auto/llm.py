"""Thin Gemini wrapper returning validated pydantic objects."""
from __future__ import annotations
import json, os, re, time
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def _call_gemini(prompt: str) -> str:
    _load_env()
    import google.generativeai as genai
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set (see .env.example)")
    genai.configure(api_key=key)
    model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))
    resp = model.generate_content(
        prompt, generation_config={"response_mime_type": "application/json", "temperature": 0.7}
    )
    return resp.text


def extract_json(text: str) -> object:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    return json.loads(text)


def generate(prompt: str, schema: Type[T], retries: int = 3, caller=_call_gemini) -> T:
    """Ask the LLM for JSON matching `schema`; retry with the error appended."""
    full = f"{prompt}\n\nReturn ONLY JSON matching this schema:\n{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
    last: Exception | None = None
    for attempt in range(retries):
        try:
            return schema.model_validate(extract_json(caller(full)))
        except (ValidationError, json.JSONDecodeError) as e:
            last = e
            full += f"\n\nPrevious answer was invalid: {str(e)[:500]}. Fix it."
        except Exception as e:  # network / quota
            last = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"LLM failed after {retries} attempts: {last}")
