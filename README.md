# LLM & AI Engineering Tasks

Four practical AI engineering projects in one repository, from structured extraction to RAG, tool-using agents and a streaming chat UI. Each task lives in its own folder with its own README, dependencies and setup instructions.

| # | Task | Folder | Stack |
|---|---|---|---|
| 1 | Structured LLM Prompt Pipeline & JSON Extractor | [`task1-resume-json-extractor`](task1-resume-json-extractor) | Python, Google Gemini, Pydantic |
| 2 | Document Q&A Assistant with RAG & Vector Embeddings | [`task2-rag-doc-qa`](task2-rag-doc-qa) | Python, LangChain, ChromaDB, local embeddings, Groq |
| 3 | Multi-Tool Autonomous AI Agent | [`task3-multi-tool-agent`](task3-multi-tool-agent) | Python, LangChain tools, DuckDuckGo search, Groq |
| 4 | Interactive Full-Stack AI Chatbot with Streamlit | [`task4-streamlit-chatbot`](task4-streamlit-chatbot) | Python, Streamlit, RAG pipeline, Groq |

## Task summaries

**Task 1: Resume JSON extractor.** Turns unstructured resume text into strictly validated JSON. It uses parameterized prompt templates with few-shot examples and Pydantic validation, and a retry loop that feeds validation errors back to the model. Inputs that are not resumes are rejected instead of filled with invented data.

**Task 2: Document Q&A with RAG.** Answers questions strictly from loaded PDFs and cites the source pages. Documents are loaded, recursively chunked, embedded locally and stored in ChromaDB; Groq generates the answers. Unrelated questions are refused.

**Task 3: Multi-tool agent.** A console agent that chooses its own tools (web search, a safe calculator, and a sandboxed file reader) and chains them to solve compound questions. An explicit agent loop prints every Thought, Action and Observation, with protection against repeated calls.

**Task 4: Streamlit chatbot.** Wraps the Task 2 RAG pipeline in a browser chat app with streaming answers, conversation memory (follow-up questions are rewritten into standalone queries), page citations, and explicit session state management.

## Repository layout

```
.
├── README.md                      <- this file
├── .gitignore                     <- shared by all tasks
├── task1-resume-json-extractor/
├── task2-rag-doc-qa/
├── task3-multi-tool-agent/
└── task4-streamlit-chatbot/
```

Each task folder contains its own `README.md`, `requirements.txt`, `.env.example` and test or demo scripts.

## Running a task

Every task is self-contained, with its **own virtual environment and its own `.env` file** (API keys are never committed). Go into a task folder and follow its README:

```bash
cd task2-rag-doc-qa      # or any other task folder
```

| Task | API key needed |
|---|---|
| 1 | Google Gemini (free key from Google AI Studio) |
| 2 | Groq (free key from console.groq.com) |
| 3 | Groq (web search needs no key) |
| 4 | Groq |

## Notes

- **Free API tiers have limits.** Task 1 was developed against Gemini's free tier of about 20 requests per day, which shaped how it was tested (see its README).
- **Model names change.** If a model returns a "not found" error, check which models your key can use and update `MODEL` / `GROQ_MODEL` in that task's `.env`.
- **No secrets are committed.** `.env` files are excluded by the shared `.gitignore`; each task ships a `.env.example` instead.
- `task2-rag-doc-qa/docs/` and `task4-streamlit-chatbot/docs/` include a test PDF of a research paper (Gao et al., 2024, available on arXiv). All rights belong to the authors.