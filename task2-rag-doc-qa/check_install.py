"""Checks that all Task 2 packages are installed and importable."""
import importlib

CHECKS = [
    ("langchain_core", "LangChain core"),
    ("langchain_community.document_loaders", "Document loaders"),
    ("langchain_text_splitters", "Text splitters"),
    ("langchain_chroma", "Chroma vector store"),
    ("langchain_huggingface", "Local embeddings"),
    ("langchain_groq", "Groq LLM"),
    ("pypdf", "PDF reading"),
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