"""Step 4: embed chunks locally and store them in ChromaDB."""
import shutil
import sys
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from ingest import load_documents, chunk_documents

PERSIST_DIR = "chroma_db"
COLLECTION = "documents"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
KEEP_KEYS = ("source", "page_number", "chunk_id")


def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)


def build_vectorstore():
    """Load PDFs, chunk them, embed the chunks, and save to ChromaDB."""
    chunks = chunk_documents(load_documents())
    for c in chunks:  # keep only the metadata we need for citations
        c.metadata = {k: c.metadata[k] for k in KEEP_KEYS if k in c.metadata}

    if Path(PERSIST_DIR).exists():
        shutil.rmtree(PERSIST_DIR)  # rebuild from scratch to avoid duplicates

    store = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION,
    )
    return store, len(chunks)


def load_vectorstore():
    """Open the existing ChromaDB store without re-embedding anything."""
    if not Path(PERSIST_DIR).exists():
        raise FileNotFoundError("No vector store found. Run: python vectorstore.py --rebuild")
    return Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=get_embeddings(),
        collection_name=COLLECTION,
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    rebuild = "--rebuild" in args
    query = " ".join(a for a in args if a != "--rebuild") or "What are the three paradigms of RAG?"

    if rebuild or not Path(PERSIST_DIR).exists():
        print("Building vector store (first run downloads the embedding model, ~90 MB)...")
        store, n = build_vectorstore()
        print(f"Stored {n} chunks in ./{PERSIST_DIR}")
    else:
        store = load_vectorstore()
        print(f"Loaded existing store ({len(store.get()['ids'])} chunks)")

    print(f"\nQuery: {query}\n")
    for rank, (doc, score) in enumerate(store.similarity_search_with_score(query, k=4), 1):
        print(f"#{rank}  distance={score:.3f}  {doc.metadata['source']}  page {doc.metadata['page_number']}")
        print("    " + doc.page_content[:250].replace("\n", " ") + "...\n")