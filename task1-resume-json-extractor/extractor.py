"""Gemini call + Pydantic validation + retry loop."""
import os
import time
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors
from pydantic import ValidationError

from prompts import build_prompt

load_dotenv()

MODEL = os.getenv("MODEL", "gemini-3.8-flash")
_client = None


class ExtractionError(Exception):
    """Raised when the model could not produce valid JSON after all retries."""


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_key_here":
            raise ExtractionError("GEMINI_API_KEY missing. Add it to your .env file.")
        _client = genai.Client(api_key=api_key)
    return _client


def _clean(raw: str) -> str:
    """Strip markdown code fences if the model added them."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()


def _call_gemini(system_instruction, contents):
    """One API call, with a short backoff on temporary errors (429/5xx)."""
    client = _get_client()
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        temperature=0,
    )
    for wait in (5, 15, 30, None):
        try:
            resp = client.models.generate_content(
                model=MODEL, contents=contents, config=config
            )
            return resp.text or ""
        except errors.APIError as e:
            if e.code in (500, 503) and wait is not None:
                print(f"  API busy ({e.code}), retrying in {wait}s...")
                time.sleep(wait)
                continue
            raise ExtractionError(f"Gemini API error: {e}") from e


def extract(text: str, schema_cls, doc_type: str = "resume", max_retries: int = 3, verbose: bool = True):
    """Extract validated data from unstructured text.

    Returns an instance of schema_cls, or raises ExtractionError.
    """
    system_instruction, contents = build_prompt(
        doc_type, schema_cls.model_json_schema(), text
    )
    last_error = None

    for attempt in range(1, max_retries + 1):
        raw = _clean(_call_gemini(system_instruction, contents))
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and data.get("error") == "not_a_resume":
                raise ExtractionError("Input does not look like a resume.")
            result = schema_cls.model_validate(data)
            if verbose:
                print(f"Attempt {attempt}: valid")
            return result
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            if verbose:
                print(f"Attempt {attempt}: FAILED validation -> retrying")
            contents.append({"role": "model", "parts": [{"text": raw}]})
            contents.append({
                "role": "user",
                "parts": [{"text": (
                    f"Your JSON failed validation with these errors:\n{e}\n"
                    "Return the corrected JSON only, following all rules. "
                    "Never use placeholder values like 'Unknown'. "
                    'If the text is not a resume, return exactly {"error": "not_a_resume"} instead.'
                )}],
            })

    raise ExtractionError(f"Failed after {max_retries} attempts. Last error: {last_error}")


if __name__ == "__main__":
    from schemas import Resume

    with open("samples/resume1.txt", encoding="utf-8") as f:
        text = f.read()

    result = extract(text, Resume)
    print(result.model_dump_json(indent=2))