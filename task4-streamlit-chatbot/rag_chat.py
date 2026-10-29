"""Step 3: RAG logic for the chat app: question rewriting, retrieval, streaming answers."""
import re

TOP_K = 8
MAX_DISTANCE = 1.25  # chunks farther than this are treated as irrelevant
NOT_FOUND_MSG = "I couldn't find the answer to that in the provided documents."

SYSTEM_PROMPT = """You are a document question-answering assistant in a chat.
Answer the user's latest question using ONLY the numbered context passages below.
The earlier conversation is only there to help you understand what the user is
referring to; never use it as a source of facts.

Rules:
- If the passages do not contain the answer, reply with exactly: NOT_FOUND
- After each statement, cite the passage(s) it came from using tags like [S1] or [S2][S3].
- Only cite tags that exist below. Do not copy bracketed reference numbers that appear
  inside the passages themselves.
- Write citation tags with ordinary square brackets, never other bracket styles.
- Be concise and accurate. Use short paragraphs or bullet points when helpful.

Context:
{context}
"""

CONDENSE_PROMPT = """Given the conversation below and the user's latest message, rewrite the
latest message as a single standalone question that can be understood without the
conversation (replace words like "it" or "the second one" with what they refer to).
If it is already standalone, return it unchanged. Return ONLY the question, with no explanation.

Conversation:
{history}

Latest message: {question}

Standalone question:"""

CITE_GROUP_RE = re.compile(r"[\[【]([^\]】]*)[\]】]")


def _text(content):
    """Message content can be a string or a list of parts; return plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(c.get("text", "") if isinstance(c, dict) else str(c) for c in content)
    return str(content)


def _clean(text):
    """Remove [S#] tags: they refer to passages of an earlier turn, not the current one."""
    return re.sub(r"\[S\d+\]", "", text).strip()


def _history_text(history, max_messages=6, max_chars=500):
    lines = []
    for m in history[-max_messages:]:
        who = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{who}: {_clean(m['content'])[:max_chars]}")
    return "\n".join(lines)


def condense_question(question, history, llm):
    """Rewrite a follow-up into a standalone question so retrieval works."""
    if not history:
        return question
    prompt = CONDENSE_PROMPT.format(history=_history_text(history), question=question)
    try:
        out = _text(llm.invoke(prompt).content).strip().strip('"')
    except Exception:
        return question
    return out if 0 < len(out) < 400 else question


def retrieve(query, store, k=TOP_K, max_distance=MAX_DISTANCE):
    results = store.similarity_search_with_score(query, k=k)
    return [(doc, score) for doc, score in results if score <= max_distance]


def format_context(hits):
    blocks = []
    for i, (doc, _score) in enumerate(hits, 1):
        m = doc.metadata
        blocks.append(f"[S{i}] ({m['source']}, page {m['page_number']})\n{doc.page_content}")
    return "\n\n".join(blocks)


def stream_answer(question, hits, history, llm):
    """Generator yielding the answer text piece by piece as the model streams it."""
    if not hits:
        yield NOT_FOUND_MSG
        return

    messages = [("system", SYSTEM_PROMPT.format(context=format_context(hits)))]
    for m in history[-6:]:
        role = "human" if m["role"] == "user" else "ai"
        messages.append((role, _clean(m["content"])[:1200]))
    messages.append(("human", question))

    head, decided = "", False
    for chunk in llm.stream(messages):
        text = _text(chunk.content).replace("【", "[").replace("】", "]")
        if not text:
            continue
        if not decided:
            # hold back the first few characters to detect a NOT_FOUND reply
            head += text
            if len(head.strip()) < len("NOT_FOUND"):
                continue
            decided = True
            if head.strip().startswith("NOT_FOUND"):
                yield NOT_FOUND_MSG
                return
            yield head
        else:
            yield text
    if not decided:  # the whole answer was very short
        yield NOT_FOUND_MSG if "NOT_FOUND" in head else head


def extract_tags(text, max_n):
    """Find cited passage numbers like [S1] or [S1, S3] in the answer."""
    nums = set()
    for group in CITE_GROUP_RE.findall(text):
        for n in re.findall(r"S(\d+)", group):
            if 1 <= int(n) <= max_n:
                nums.add(int(n))
    return sorted(nums)


def sources_from_answer(answer, hits):
    """Map cited tags to real file names and page numbers from the chunk metadata."""
    sources = []
    for n in extract_tags(answer, len(hits)):
        doc = hits[n - 1][0]
        sources.append({
            "tag": f"S{n}",
            "source": doc.metadata["source"],
            "page": doc.metadata["page_number"],
            "snippet": doc.page_content[:300].replace("\n", " "),
        })
    return sources