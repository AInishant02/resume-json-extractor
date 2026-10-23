"""Step 3: the agent loop (thought -> action -> observation -> final answer)."""
import json
import os
import sys
from datetime import date

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_groq import ChatGroq

from tools import TOOLS, TOOLS_BY_NAME

load_dotenv()

MAX_STEPS = 8
OBS_PREVIEW_CHARS = 600
GATHER_CHARS = 800

SYSTEM_PROMPT = f"""You are a research assistant agent. Today's date is {date.today().isoformat()}.
Tools: web_search (current or external facts), calculator (all arithmetic),
read_file and list_files (local files in the workspace folder).

Rules:
- Use tools whenever they help. Never do arithmetic in your head; always use the calculator.
- Never guess the contents of a local file; read it. If unsure of a file name, call list_files.
- Use web_search for facts that may be current or that you are not certain of.
- Every tool call needs a short 'thought' explaining why you are making it.
- Break compound questions into steps and use several tools in sequence if needed.
- Approximate figures are fine. As soon as a search result contains a usable number,
  use it and state its source and year. Never repeat a search that already returned results,
  and make at most 2 searches for the same fact.
- If a tool returns an error, adapt: fix the input or try another approach.
- If a search fails or finds nothing, try at most one differently worded query; after that, answer with what you have and say what you could not find.
- Only name a source (website or file) if its name or URL appeared in a tool result.
- If the question needs no tool (such as a greeting), answer directly.
- Your final answer must be concise and mention which files or URLs you used.
"""


def tool_schemas_with_thought():
    """Tool schemas with an extra required 'thought' argument, so every action
    comes with the model's own stated reason."""
    schemas = []
    for t in TOOLS:
        schema = convert_to_openai_tool(t)
        params = schema["function"]["parameters"]
        params.setdefault("properties", {})["thought"] = {
            "type": "string",
            "description": "One short sentence: why you are calling this tool and what you expect to learn.",
        }
        params.setdefault("required", []).append("thought")
        schemas.append(schema)
    return schemas


def text_of(content):
    """Message content can be a string or a list of parts; return plain text."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [c.get("text", "") if isinstance(c, dict) else str(c) for c in content]
        return " ".join(parts).strip()
    return str(content).strip()


def run_agent(question, llm, llm_with_tools):
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=question)]
    gathered = []
    seen_calls = set()
    print(f"\nQuestion: {question}")

    for step in range(1, MAX_STEPS + 1):
        ai = llm_with_tools.invoke(messages)
        messages.append(ai)
        spoken = text_of(ai.content)

        if not ai.tool_calls:  # no tool requested -> this is the final answer
            print(f"\n=== Final Answer ===\n{spoken}")
            return spoken

        print(f"\n--- Step {step} ---")
        for call in ai.tool_calls:
            name = call["name"]
            args = dict(call["args"])
            thought = str(args.pop("thought", "") or spoken or "(none given)")
            print(f"Thought: {thought}")
            print(f"Action: {name}({json.dumps(args, ensure_ascii=False)})")

            key = (name, json.dumps(args, sort_keys=True, ensure_ascii=False))
            tool = TOOLS_BY_NAME.get(name)
            if key in seen_calls:
                observation = (
                    "Duplicate call: you already made this exact call. Use the earlier "
                    "result, or give your final answer with what you have."
                )
            elif tool is None:
                observation = f"Error: unknown tool '{name}'. Available: {', '.join(TOOLS_BY_NAME)}"
            else:
                seen_calls.add(key)
                try:
                    observation = str(tool.invoke(args))
                except Exception as e:
                    observation = f"Error: tool '{name}' failed ({e})."

            shown = observation
            if len(shown) > OBS_PREVIEW_CHARS:
                shown = shown[:OBS_PREVIEW_CHARS] + " ...[truncated in display]"
            print("Observation: " + shown.replace("\n", "\n             "))

            gathered.append(
                f"- {name}({json.dumps(args, ensure_ascii=False)}) returned: {observation[:GATHER_CHARS]}"
            )
            messages.append(ToolMessage(content=observation, tool_call_id=call["id"]))

    # Step limit reached: answer from the gathered observations, with no tools involved
    print(f"\n(Stopped after {MAX_STEPS} steps; answering from what was gathered.)")
    summary_messages = [
        SystemMessage(content=(
            "You are a research assistant. Answer using only the information provided below. "
            "Do not call tools. Be concise, and say what is missing or uncertain."
        )),
        HumanMessage(content=f"Question: {question}\n\nInformation gathered so far:\n" + "\n".join(gathered)),
    ]
    final = text_of(llm.invoke(summary_messages).content)
    print(f"\n=== Final Answer ===\n{final}")
    return final


def main():
    model = os.getenv("GROQ_MODEL")
    if not model or not os.getenv("GROQ_API_KEY"):
        sys.exit("GROQ_API_KEY or GROQ_MODEL missing. Check your .env file.")

    llm = ChatGroq(model=model, temperature=0)
    llm_with_tools = llm.bind_tools(tool_schemas_with_thought())

    def run(question):
        try:
            run_agent(question, llm, llm_with_tools)
        except Exception as e:
            print(f"\nError: {e}")

    if len(sys.argv) > 1:  # one-shot: python agent.py "your question"
        run(" ".join(sys.argv[1:]))
        return

    print(f"Multi-tool agent ready (model: {model}). Type 'exit' to quit.")
    while True:
        question = input("\nYou: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if question:
            run(question)


if __name__ == "__main__":
    main()