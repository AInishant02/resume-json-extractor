# Document Q&A Assistant with RAG & Vector Embeddings

A Retrieval-Augmented Generation (RAG) pipeline that answers questions **strictly from loaded PDF/text documents** and cites the source pages. It loads documents with LangChain, chunks them recursively, embeds the chunks locally, stores them in ChromaDB, and uses Groq to generate answers from the retrieved context.

## How it works

```
PDF/TXT -> load pages -> recursive chunking -> local embeddings -> ChromaDB
                                                                      |
question -> embed -> retrieve top-K chunks -> prompt with [S1]..[Sn] passages -> Groq LLM
                                                                      |
                              answer with [S#] tags -> mapped to real file + page numbers
```

1. **Load** (`ingest.py`): `PyPDFLoader` / `TextLoader`, one document per page, with source file and 1-based page number in the metadata. The bibliography is skipped.
2. **Chunk** (`ingest.py`): `RecursiveCharacterTextSplitter`, 1000 characters with 200 overlap.
3. **Embed and store** (`vectorstore.py`): local `sentence-transformers/all-MiniLM-L6-v2` embeddings saved in a persistent ChromaDB store.
4. **Retrieve and answer** (`rag.py`): the 8 closest chunks (within a distance cutoff) are put into a prompt as numbered passages. The model must answer only from them, cite tags like `[S2]`, or reply `NOT_FOUND`.
5. **Citations**: the model only writes passage tags. The page numbers shown to the user come from the chunk metadata, so the model cannot invent page numbers.

## Setup

**Requirements:** Python 3.10+ and a free Groq API key (console.groq.com).

```bash
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # macOS/Linux: cp .env.example .env
```

Fill in `.env`:

```
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

Run `python test_groq.py` to list the models your key can use and to check the connection.

Put one or more PDF/TXT files in `docs/`. The test document included in this repo is *"Retrieval-Augmented Generation for Large Language Models: A Survey"* (Gao et al., 2024, available on arXiv), saved as `docs/new_rag_pdf.pdf`. All rights to its content belong to the authors.

## Usage

```bash
python vectorstore.py --rebuild          # load, chunk, embed and store the documents
python rag.py "What are the three paradigms of RAG?"   # one question
python rag.py                            # interactive mode (type 'exit' to quit)
python run_tests.py                      # run the test questions, save test_results.md
```

Example output:

```
Answer:
The three RAG paradigms are Naive RAG, Advanced RAG, and Modular RAG [S1]

Sources:
  [S1] new_rag_pdf.pdf, page 2
```

## Project structure

```
requirements.txt
.env.example
check_install.py   # verifies packages are installed
test_groq.py       # lists Groq models and tests the connection
ingest.py          # loading + recursive chunking
vectorstore.py     # embeddings + ChromaDB (build / load / search)
rag.py             # retrieval + generation + page citations
run_tests.py       # test question runner
docs/              # input documents
chroma_db/         # generated vector store (not committed)
```

## Results

The 7 test questions: 5 answerable from the document, 2 deliberately unrelated.

| # | Question | Expected | Behaviour | Pages cited | Check |
|---|---|---|---|---|---|
| 1 | What are the three paradigms of RAG? | answer with citations | answered | 2 | PASS |
| 2 | What is the difference between Naive RAG and Advanced RAG? | answer with citations | answered | 2, 4 | PASS |
| 3 | How is retrieval evaluated? | answer with citations | answered | 12 | PASS |
| 4 | What is Self-RAG? | answer with citations | answered | 5 | PASS |
| 5 | What problems does RAG help solve in large language models? | answer with citations | answered | 1, 14 | PASS |
| 6 | Who won the 2022 FIFA World Cup? | refuse | refused | - | PASS |
| 7 | What is the capital of France? | refuse | refused | - | PASS |

All 7 behaved as expected. Cited pages were spot-checked against the PDF for two of the answers. Full answers are in `test_results.md`.

## Design decisions and lessons learned

- **No `RetrievalQA`.** The suggested `RetrievalQA` chain is deprecated in LangChain, which recommends `create_retrieval_chain`. The retrieve, prompt and generate steps are written out directly here, which keeps the code short and gives full control over citations.
- **Local embeddings.** Embeddings run on the user's machine, so indexing costs nothing and uses no API quota. Only the answer generation calls Groq.
- **The bibliography is skipped.** In an early test, a question about evaluation returned reference-list entries because paper titles contain the same keywords. These chunks carry no answers, so everything after the "References" heading is dropped (chunks fell from 144 to 98).
- **Citations are mapped from metadata.** The model is only asked to cite passage tags, and the real file and page come from the stored metadata.
- **The model's bracket style needed handling.** The model wrote some citation tags with fullwidth brackets (`【S1】`), which the first parser missed and which made correct answers fail the tests. The parser now accepts both styles, and the prompt asks for plain brackets.
- **Retrieval settings were tuned from a failure.** "What is Self-RAG?" was refused at first because the retriever ranked generic RAG passages above the relevant chunk (Self-RAG is a rare term). Widening retrieval from 5 to 8 chunks and loosening the distance cutoff fixed it, while the two out-of-scope questions were still refused.
- **Two layers of refusal.** Chunks beyond the distance cutoff are dropped before the LLM sees them, and the prompt tells the LLM to reply `NOT_FOUND` if the passages don't contain the answer.

## Known limitations

- Embedding-based retrieval can miss rare names and exact terms. Adding keyword (hybrid) search would help.
- Only text-based PDFs are supported. Scanned documents would need OCR, and figures and tables are not read.
- Text extraction from two-column papers can leave broken words and hyphenation.
- The distance cutoff and `TOP_K` were tuned on one document and may need adjusting for others.
- `langchain-community` prints a deprecation warning about its planned sunset, which is harmless for now.