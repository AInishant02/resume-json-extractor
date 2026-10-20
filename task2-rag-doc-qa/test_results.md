# RAG test results

Model: `openai/gpt-oss-120b`

| # | Question | Expected | Behaviour | Pages cited | Check |
|---|---|---|---|---|---|
| 1 | What are the three paradigms of RAG? | answer with citations | answered | 2 | PASS |
| 2 | What is the difference between Naive RAG and Advanced RAG? | answer with citations | answered | 2, 4 | PASS |
| 3 | How is retrieval evaluated? | answer with citations | answered | 12 | PASS |
| 4 | What is Self-RAG? | answer with citations | answered | 5 | PASS |
| 5 | What problems does RAG help solve in large language models? | answer with citations | answered | 1, 14 | PASS |
| 6 | Who won the 2022 FIFA World Cup? | refuse | refused | - | PASS |
| 7 | What is the capital of France? | refuse | refused | - | PASS |

**7/7 behaved as expected.**

## Full answers

### 1. What are the three paradigms of RAG?

The three RAG paradigms are **Naive RAG, Advanced RAG, and Modular RAG**[S1]

- [S1] new_rag_pdf.pdf, page 2

### 2. What is the difference between Naive RAG and Advanced RAG?

Naive RAG is the earliest, simple pipeline that mainly consists of three sequential steps—indexing, retrieval, and generation—without additional refinements. Advanced RAG extends this basic chain by introducing multiple optimization strategies around the pre‑retrieval and post‑retrieval stages, adding extra processing before and after the core retrieval step while still following a chain‑like structure[S1][S4]

- [S1] new_rag_pdf.pdf, page 2
- [S4] new_rag_pdf.pdf, page 4

### 3. How is retrieval evaluated?

Retrieval is assessed through “retrieval quality” metrics that come from search‑engine, recommendation‑system and information‑retrieval research. Commonly used measures include Hit Rate, Mean Reciprocal Rank (MRR) and Normalized Discounted Cumulative Gain (NDCG) to gauge how effectively the retriever supplies relevant context[S4]

- [S4] new_rag_pdf.pdf, page 12

### 4. What is Self-RAG?

Self‑RAG is an adaptive‑retrieval technique used in Modular RAG that evaluates whether retrieval is needed for a given scenario, allowing the system to go beyond a fixed retrieval process. [S8]

- [S8] new_rag_pdf.pdf, page 5

### 5. What problems does RAG help solve in large language models?

RAG lets large language models pull in external knowledge, which cuts down on hallucinated or factually‑incorrect output and makes the models more useful for real‑world tasks such as chatbots[S4].  
By retrieving relevant passages on demand, RAG also lets the model point to its sources so users can verify answers, and it avoids the slowdown that occurs when a model tries to process a huge amount of context all at once, because chunked retrieval and on‑demand input improve inference efficiency[S7].

- [S4] new_rag_pdf.pdf, page 1
- [S7] new_rag_pdf.pdf, page 14

### 6. Who won the 2022 FIFA World Cup?

I couldn't find the answer to that in the provided documents.


### 7. What is the capital of France?

I couldn't find the answer to that in the provided documents.

