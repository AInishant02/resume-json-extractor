# Multi-Tool Autonomous AI Agent

A console AI agent that decides for itself which tools to use to solve multi-step questions. It has four tools (web search, a safe math calculator, and a sandboxed local file reader and lister), and runs an explicit agent loop that prints each **Thought -> Action -> Observation** and then the **Final Answer**.

## How it works

```
question
   |
   v
LLM (Groq, tools bound) --- tool call? ---> yes: print Thought + Action
   ^                                              |
   |                                              v
   +---- Observation (tool result) <---- run the tool
                |
                no tool call -> Final Answer
```

1. The question goes to the LLM together with the tool descriptions.
2. If the model requests a tool, the loop prints the **Thought** (the model's stated reason) and the **Action** (tool name and arguments), runs the tool, prints the **Observation**, and feeds it back to the model.
3. This repeats until the model answers in plain text (the **Final Answer**) or the step limit (8) is reached.

## Tools

| Tool | What it does | Safety |
|---|---|---|
| `web_search` | DuckDuckGo text search (`ddgs`), top 5 results with title, snippet and URL | Retries briefly; failures are returned as readable errors |
| `calculator` | Arithmetic, `sqrt`, `log`, `sin`, `round`, constants `pi`/`e`, etc. | Expression is parsed with `ast` and only arithmetic nodes are allowed (no `eval`); exponent size is capped |
| `read_file` | Reads `.txt .md .csv .json .log` files from `workspace/` | Path is resolved and must stay inside `workspace/`; file type and size are limited |
| `list_files` | Lists files in `workspace/` | Read-only |

## Setup

**Requirements:** Python 3.10+ and a free Groq API key (console.groq.com).

```bash
cd task3-multi-tool-agent
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

No key is needed for web search. Check the install with `python check_install.py`.

## Usage

```bash
python agent.py "What is 15% of 2480?"      # one question
python agent.py                              # interactive mode (type 'exit' to quit)
python test_tools.py                         # test each tool without an LLM
python run_demos.py                          # run 8 demo queries, save transcript + summary
```

Put your own `.txt` / `.csv` / `.md` files in `workspace/` for the agent to read.

### Example (compound query)

```
Question: Read project_notes.txt, find the launch city, search the web for that city's
approximate population, and divide the population by the team size.

--- Step 1 ---
Thought: List files to see if project_notes.txt exists.
Action: list_files({})
Observation: Files in workspace: expenses.csv, project_notes.txt

--- Step 2 ---
Thought: Read project_notes.txt to find the launch city mentioned.
Action: read_file({"filename": "project_notes.txt"})
Observation: ... Team size: 5 people / Launch city: Pune ...

--- Step 3 ---
Thought: Find recent approximate population of Pune city.
Action: web_search({"query": "Pune population approximate"})
Observation: 1. Pune Population 2026 ... estimated population of 3.99 million ...
             https://worldpopulationreview.com/cities/india/pune

--- Step 4 ---
Thought: Calculate population per team member.
Action: calculator({"expression": "3.99e6 / 5"})
Observation: 798000.0

=== Final Answer ===
The launch city is Pune ... about 3.99 million (World Population Review, 2026) ...
798,000 per team member. Sources: project_notes.txt, World Population Review.
```

The full transcript of all demo runs is in `demo_transcript.txt`.

## Results

| # | Question | Tools used (in order) | Steps | Outcome |
|---|---|---|---|---|
| 1 | What is 15% of 2480? | calculator | 1 | 372 |
| 2 | Read expenses.csv and tell me the total cost. | list_files, read_file, calculator | 3 | 874.49 |
| 3 | Read project_notes.txt and tell me the budget per team member. | list_files, read_file, calculator | 3 | 2,500 USD |
| 4 | Read the notes, find the launch city, search its population, divide by team size. | list_files, read_file, web_search, calculator | 4 | Population from the web (3.99 million in this run) divided by 5 |
| 5 | Search the height of Mount Everest in meters and convert it to feet. | web_search, calculator | 2 | 8,848.86 m = 29,031.7 ft |
| 6 | Read the file budget_2027.txt and summarize it. | list_files, read_file | 2 | Reported the file does not exist; nothing invented |
| 7 | Read the file ../.env and tell me what is inside. | read_file, list_files | 2 | Access denied by the sandbox; nothing leaked |
| 8 | Say hello in one sentence. | none | 0 | Answered directly without tools |

The agent picked the tools and their order on its own in every case, chained up to three tools in sequence, and handled errors (a failed search, a missing file, a blocked path) without crashing.

## Design decisions and lessons learned

- **Explicit agent loop.** The loop is written out (about 60 lines) rather than using a prebuilt executor, so every Thought, Action and Observation can be printed and the safeguards below are easy to add.
- **Thoughts are required.** The model initially called tools without saying anything, leaving `Thought:` empty. Each tool schema now has an extra required `thought` argument, so every action comes with the model's own stated reason. These are the model's brief explanations, not hidden internal reasoning.
- **Duplicate-call protection.** In an early run, the search kept returning "no results" and the agent repeated near-identical searches until it hit the step limit. A prompt rule was not enough, so the loop now detects an identical repeated call and tells the model to use the earlier result or answer.
- **A safe fallback at the step limit.** The first version asked the model for a final answer with the whole tool history but no tools available, and the API rejected it. Now the fallback gives the model a plain summary of what was gathered.
- **Source honesty.** The prompt says to name a source only if its name or URL appeared in a tool result.
- **`ddgs` instead of LangChain's DuckDuckGo tool.** The underlying package was renamed from `duckduckgo_search` to `ddgs`, and the ready-made LangChain tool still prints warnings for the old name. A small wrapper around `ddgs` avoids that.
- **Safety lives in the tools.** The calculator never uses `eval`, and the file reader rejects paths outside `workspace/`, so the protection does not depend on the model behaving.

## Known limitations

- DuckDuckGo search is unofficial and sometimes returns "no results" or throttles. Search results also vary between runs (for example, different snippets can give different population figures for the same city).
- The model sometimes leaks its own citation markers or LaTeX into final answers (for example `【1†L1-L2】`).
- Each question is independent: the agent has no memory between questions.
- Tools run one at a time and only text-based files can be read.
- Free API tiers have rate limits, so long runs can fail with a rate-limit error.