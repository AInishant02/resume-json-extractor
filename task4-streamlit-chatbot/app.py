"""Streamlit chat app wrapping the RAG pipeline (polished version)."""
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from rag_chat import TOP_K, condense_question, retrieve, sources_from_answer, stream_answer
from vectorstore import PERSIST_DIR, build_vectorstore, load_vectorstore

load_dotenv()

EXAMPLES = [
    "What are the three paradigms of RAG?",
    "How is retrieval evaluated?",
    "What is Self-RAG?",
]

st.set_page_config(page_title="Document Chat", page_icon="📄")
st.title("📄 Chat with your documents")
st.caption("Answers come only from the loaded PDFs, with page citations.")


@st.cache_resource(show_spinner="Loading documents and the embedding model...")
def get_store():
    if not Path(PERSIST_DIR).exists():
        build_vectorstore()
    return load_vectorstore()


@st.cache_resource
def get_llm():
    model = os.getenv("GROQ_MODEL")
    if not model or not os.getenv("GROQ_API_KEY"):
        return None
    return ChatGroq(model=model, temperature=0)


def friendly_error(e):
    msg = str(e)
    if "429" in msg or "rate limit" in msg.lower():
        return "The model is rate-limited right now. Please wait a minute and try again."
    if "401" in msg or "invalid api key" in msg.lower():
        return "The Groq API key was rejected. Check GROQ_API_KEY in your .env file."
    return f"Something went wrong: {msg}"


def transcript_md(messages):
    lines = ["# Chat transcript", ""]
    for m in messages:
        who = "You" if m["role"] == "user" else "Assistant"
        lines.append(f"**{who}:** {m['content']}")
        for s in m.get("sources") or []:
            lines.append(f"- [{s['tag']}] {s['source']}, page {s['page']}")
        lines.append("")
    return "\n".join(lines)


def show_sources(sources):
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})"):
        for s in sources:
            st.markdown(f"**[{s['tag']}] {s['source']}, page {s['page']}**")
            st.caption(s["snippet"] + "...")


llm = get_llm()
if llm is None:
    st.error("GROQ_API_KEY or GROQ_MODEL is missing. Add them to your .env file and restart.")
    st.stop()
store = get_store()

# Session state: one conversation per browser session
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("Session")
    st.write(f"Model: `{os.getenv('GROQ_MODEL')}`")
    docs = sorted(p.name for p in Path("docs").glob("*") if p.suffix.lower() in {".pdf", ".txt"})
    st.write("Documents: " + (", ".join(docs) or "none"))
    st.write(f"Indexed chunks: {len(store.get()['ids'])}")
    top_k = st.slider("Passages retrieved per question", 3, 10, TOP_K)
    counter = st.empty()  # filled at the end of the script, once this run's messages are known

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if st.session_state.messages:
        st.download_button(
            "⬇️ Download transcript",
            transcript_md(st.session_state.messages),
            file_name="chat_transcript.md",
            use_container_width=True,
        )

    st.divider()
    st.subheader("Try an example")
    for q in EXAMPLES:
        if st.button(q, key=f"ex_{q}", use_container_width=True):
            st.session_state.pending = q

# ------------------------------------------- re-draw the conversation each run
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("searched"):
            st.caption(f"Searching for: *{msg['searched']}*")
        st.markdown(msg["content"])
        show_sources(msg.get("sources"))

# --------------------------------------------------------- handle a question
typed = st.chat_input("Ask a question about the documents...")
question = typed or st.session_state.pop("pending", None)

if question:
    # conversation so far, without failed turns
    history = [m for m in st.session_state.messages if not m.get("error")]
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        searched, sources, failed = None, [], False
        try:
            standalone = condense_question(question, history, llm)
            if standalone != question:
                searched = standalone
                st.caption(f"Searching for: *{searched}*")
            hits = retrieve(standalone, store, k=top_k)
            reply = st.write_stream(stream_answer(question, hits, history, llm))
            sources = sources_from_answer(reply, hits)
            show_sources(sources)
        except Exception as e:
            reply, failed = friendly_error(e), True
            st.error(reply)

    st.session_state.messages.append(
        {"role": "assistant", "content": reply, "sources": sources,
         "searched": searched, "error": failed}
    )

counter.write(f"Messages in this session: {len(st.session_state.messages)}")