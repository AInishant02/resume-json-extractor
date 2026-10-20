"""Smoke test: confirms your Gemini API key and model name work."""
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_key_here":
    raise SystemExit("GEMINI_API_KEY missing. Paste your key into .env first.")

client = genai.Client(api_key=api_key)
resp = client.models.generate_content(
    model=os.getenv("MODEL", "gemini-2.5-flash"),
    contents="Reply with the single word: ready",
)
print(resp.text)
