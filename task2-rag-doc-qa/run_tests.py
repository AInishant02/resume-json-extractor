"""Step 7: run a fixed set of test questions and save the results for the README."""
import os
import sys

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from rag import ask, NOT_FOUND_MSG
from vectorstore import load_vectorstore

load_dotenv()

# (question, should the PDF contain the answer?)
TESTS = [
    ("What are the three paradigms of RAG?", True),
    ("What is the difference between Naive RAG and Advanced RAG?", True),
    ("How is retrieval evaluated?", True),
    ("What is Self-RAG?", True),
    ("What problems does RAG help solve in large language models?", True),
    ("Who won the 2022 FIFA World Cup?", False),
    ("What is the capital of France?", False),
]


def main():
    model = os.getenv("GROQ_MODEL")
    if not model:
        sys.exit("GROQ_MODEL missing. Add it to .env.")

    store = load_vectorstore()
    llm = ChatGroq(model=model, temperature=0)

    summary = [
        "| # | Question | Expected | Behaviour | Pages cited | Check |",
        "|---|---|---|---|---|---|",
    ]
    details = []
    passed = 0

    for i, (question, answerable) in enumerate(TESTS, 1):
        print(f"\n[{i}/{len(TESTS)}] {question}")
        try:
            result = ask(question, store, llm)
        except Exception as e:
            print(f"  ERROR: {e}")
            summary.append(f"| {i} | {question} | - | error | - | FAIL |")
            continue

        found = result["answer"] != NOT_FOUND_MSG
        pages = ", ".join(str(s["page"]) for s in result["sources"]) or "-"
        ok = (found and bool(result["sources"])) if answerable else (not found)
        passed += ok

        expected = "answer with citations" if answerable else "refuse"
        behaviour = "answered" if found else "refused"
        status = "PASS" if ok else "FAIL"
        print(f"  {status}: {behaviour}, pages: {pages}")
        print("  " + result["answer"][:200].replace("\n", " "))

        summary.append(
            f"| {i} | {question} | {expected} | {behaviour} | {pages} | {status} |"
        )
        details.append(f"### {i}. {question}\n\n{result['answer']}\n")
        for s in result["sources"]:
            details[-1] += f"\n- [{s['tag']}] {s['source']}, page {s['page']}"
        details[-1] += "\n"

    report = (
        f"# RAG test results\n\nModel: `{model}`\n\n"
        + "\n".join(summary)
        + f"\n\n**{passed}/{len(TESTS)} behaved as expected.**\n\n"
        + "## Full answers\n\n"
        + "\n".join(details)
    )
    with open("test_results.md", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n{passed}/{len(TESTS)} behaved as expected. Saved to test_results.md")


if __name__ == "__main__":
    main()