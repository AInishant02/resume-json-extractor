"""Step 6: answer questions strictly from the documents, with page citations."""
import os
import re
import sys

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from vectorstore import load_vectorstore

load_dotenv()

TOP_K = 8
MAX_DISTANCE = 1.25  # chunks farther than this are treated as irrelevant
NOT_FOUND_MSG = "I couldn't find the answer to that in the provided documents."

SYSTEM_PROMPT = """You are a document question-answering assistant.
Answer the user's question using ONLY the numbered context passages below.

Rules:
- Do not use outside knowledge. If the passages do not contain the answer,
  reply with exactly: NOT_FOUND
- After each statement, cite the passage(s) it came from using tags like [S1] or [S2][S3].
- Only cite tags that exist below. Do not copy bracketed reference numbers
  that appear inside the passages themselves.
- Write citation tags with ordinary square brackets, for example [S1], never other bracket styles.
- Be concise and accurate.

Context:
{context}
"""


def format_context(hits):
    blocks = []
    for i, (doc, _score) in enumerate(hits, 1):
        m = doc.metadata
        blocks.append(f"[S{i}] ({m['source']}, page {m['page_number']})\n{doc.page_content}")
    return "\n\n".join(blocks)

CITE_GROUP_RE = re.compile(r"[\[【]([^\]】]*)[\]】]")


def extract_tags(text, max_n):
    """Find cited passage numbers like [S1], 【S2】 or [S1, S3] in the answer."""
    nums = set()
    for group in CITE_GROUP_RE.findall(text):
        for n in re.findall(r"S(\d+)", group):
            if 1 <= int(n) <= max_n:
                nums.add(int(n))
    return sorted(nums)

def ask(question, store, llm, k=TOP_K):
    """Return {"answer": str, "sources": [{"tag", "source", "page"}, ...]}."""
    results = store.similarity_search_with_score(question, k=k)
    hits = [(doc, score) for doc, score in results if score <= MAX_DISTANCE]
    if not hits:
        return {"answer": NOT_FOUND_MSG, "sources": []}

    messages = [
        ("system", SYSTEM_PROMPT.format(context=format_context(hits))),
        ("human", question),
    ]
    answer = llm.invoke(messages).content.strip()
    if "NOT_FOUND" in answer:
        return {"answer": NOT_FOUND_MSG, "sources": []}

    answer = answer.replace("【", "[").replace("】", "]")
    cited = extract_tags(answer, len(hits))
    sources = []
    for n in cited:
        meta = hits[n - 1][0].metadata
        sources.append(
            {"tag": f"S{n}", "source": meta["source"], "page": meta["page_number"]}
        )
    return {"answer": answer, "sources": sources}


def print_result(result):
    print("\nAnswer:\n" + result["answer"])
    if result["sources"]:
        print("\nSources:")
        for s in result["sources"]:
            print(f"  [{s['tag']}] {s['source']}, page {s['page']}")


def main():
    model = os.getenv("GROQ_MODEL")
    if not model:
        sys.exit("GROQ_MODEL missing. Add it to .env (see test_groq.py).")

    store = load_vectorstore()
    llm = ChatGroq(model=model, temperature=0)

    def run(question):
        try:
            print_result(ask(question, store, llm))
        except Exception as e:
            print(f"\nError: {e}")

    if len(sys.argv) > 1:  # one-shot: python rag.py "your question"
        run(" ".join(sys.argv[1:]))
        return

    print("Ask questions about your documents. Type 'exit' to quit.")
    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if question:
            run(question)


if __name__ == "__main__":
    main()