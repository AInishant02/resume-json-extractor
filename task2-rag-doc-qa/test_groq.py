"""Step 5: list the Groq models your key can use, and test the one in .env."""
import os

from dotenv import load_dotenv
from groq import Groq
from langchain_groq import ChatGroq

load_dotenv()
key = os.getenv("GROQ_API_KEY")
if not key or key == "your_key_here":
    raise SystemExit("GROQ_API_KEY missing. Add your key to .env first.")

client = Groq(api_key=key)
ids = sorted(m.id for m in client.models.list().data)
print("Models available to your key:")
for model_id in ids:
    print("  ", model_id)

model = os.getenv("GROQ_MODEL")
if not model:
    print("\nNext: add a line GROQ_MODEL=<one of the ids above> to .env, then run this again.")
else:
    print(f"\nTesting {model} ...")
    llm = ChatGroq(model=model, temperature=0)
    print(llm.invoke("Reply with the single word: ready").content)