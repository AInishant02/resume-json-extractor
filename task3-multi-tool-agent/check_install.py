"""Checks that all Task 3 packages are installed and importable."""
import importlib

CHECKS = [
    ("langchain_core.tools", "LangChain tools"),
    ("langchain_core.messages", "LangChain messages"),
    ("langchain_groq", "Groq LLM"),
    ("ddgs", "DuckDuckGo search"),
    ("dotenv", "python-dotenv"),
]

failed = 0
for module, label in CHECKS:
    try:
        importlib.import_module(module)
        print(f"OK      {label}")
    except Exception as e:
        failed += 1
        print(f"FAILED  {label}: {e}")

print("\nAll good!" if failed == 0 else f"\n{failed} problem(s) above.")