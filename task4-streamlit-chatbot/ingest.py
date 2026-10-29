"""Step 3: load PDF/text documents and split them into chunks."""
import re
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

DOCS_DIR = Path("docs")
REFERENCES_RE = re.compile(r"^\s*references\s*$", re.IGNORECASE | re.MULTILINE)

def load_documents(docs_dir=DOCS_DIR, drop_references=True):
    """Load every .pdf/.txt in docs_dir. Returns one Document per PDF page.

    If drop_references is True, everything from a 'References' heading onward
    is skipped, because bibliography entries add noise to retrieval.
    """
    files = sorted(
        p for p in Path(docs_dir).glob("*") if p.suffix.lower() in {".pdf", ".txt"}
    )
    if not files:
        raise FileNotFoundError(f"No .pdf or .txt files found in {docs_dir}/")

    docs = []
    for path in files:
        if path.suffix.lower() == ".pdf":
            pages = PyPDFLoader(str(path)).load()
        else:
            pages = TextLoader(str(path), encoding="utf-8").load()

        for i, page in enumerate(pages):
            page.metadata["source"] = path.name
            page.metadata["page_number"] = page.metadata.get("page", i) + 1

            if drop_references:
                match = REFERENCES_RE.search(page.page_content)
                if match:
                    page.page_content = page.page_content[: match.start()]
                    if page.page_content.strip():
                        docs.append(page)
                    print(
                        f"Note: references start on page {page.metadata['page_number']} "
                        f"of {path.name}; skipping the rest."
                    )
                    break
            docs.append(page)
    return docs


def chunk_documents(docs, chunk_size=1000, chunk_overlap=200):
    """Split pages into overlapping chunks, keeping source/page metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
    return chunks


if __name__ == "__main__":
    docs = load_documents()
    total_chars = sum(len(d.page_content) for d in docs)
    empty = sum(1 for d in docs if len(d.page_content.strip()) < 20)

    print(f"Pages loaded:      {len(docs)}")
    print(f"Total characters:  {total_chars}")
    print(f"Near-empty pages:  {empty}")
    if docs and total_chars / len(docs) < 200:
        print("WARNING: very little text per page. Is this a scanned PDF?")

    chunks = chunk_documents(docs)
    avg = sum(len(c.page_content) for c in chunks) / len(chunks)
    print(f"\nChunks created:    {len(chunks)}")
    print(f"Average chunk len: {avg:.0f} characters")

    for label, chunk in (("FIRST", chunks[0]), ("MIDDLE", chunks[len(chunks) // 2])):
        print(f"\n--- {label} CHUNK ---")
        print("metadata:", chunk.metadata)
        print(chunk.page_content[:300])