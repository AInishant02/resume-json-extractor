"""Step 4: run demo queries, save the full transcript and a summary table."""
import io
import os
import re
import sys
import time

from langchain_groq import ChatGroq

from agent import run_agent, tool_schemas_with_thought  # agent.py also loads .env

QUERIES = [
    "What is 15% of 2480?",
    "Read expenses.csv and tell me the total cost.",
    "Read project_notes.txt and tell me the budget per team member.",
    "Read project_notes.txt, find the launch city, search the web for that city's "
    "approximate population, and divide the population by the team size.",
    "Search the web for the height of Mount Everest in meters and convert it to feet.",
    "Read the file budget_2027.txt and summarize it.",
    "Read the file ../.env and tell me what is inside.",
    "Say hello in one sentence.",
]


class Tee:
    """Write to several streams at once (console + buffer)."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)

    def flush(self):
        for s in self.streams:
            s.flush()


def main():
    model = os.getenv("GROQ_MODEL")
    if not model or not os.getenv("GROQ_API_KEY"):
        sys.exit("GROQ_API_KEY or GROQ_MODEL missing. Check your .env file.")

    llm = ChatGroq(model=model, temperature=0)
    llm_with_tools = llm.bind_tools(tool_schemas_with_thought())

    transcript = [f"Agent demo transcript (model: {model})\n"]
    rows = [
        "| # | Question | Tools used (in order) | Steps | Result |",
        "|---|---|---|---|---|",
    ]

    for i, question in enumerate(QUERIES, 1):
        print("\n" + "=" * 70 + f"\nDEMO {i}/{len(QUERIES)}\n" + "=" * 70)
        buf, real = io.StringIO(), sys.stdout
        sys.stdout = Tee(real, buf)
        try:
            run_agent(question, llm, llm_with_tools)
        except Exception as e:
            print(f"\nError: {e}")
        finally:
            sys.stdout = real

        text = buf.getvalue()
        transcript.append("=" * 70 + f"\nDEMO {i}\n" + "=" * 70 + text)

        tools_used = re.findall(r"^Action: (\w+)\(", text, re.M)
        steps = len(re.findall(r"^--- Step \d+ ---", text, re.M))
        ok = "=== Final Answer ===" in text
        rows.append(
            f"| {i} | {question} | {' -> '.join(tools_used) or 'none'} | {steps} | "
            f"{'answered' if ok else 'ERROR'} |"
        )
        time.sleep(3)  # be gentle with rate limits

    with open("demo_transcript.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(transcript))
    with open("demo_summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")

    print("\n" + "\n".join(rows))
    print("\nSaved demo_transcript.txt and demo_summary.md")


if __name__ == "__main__":
    main()