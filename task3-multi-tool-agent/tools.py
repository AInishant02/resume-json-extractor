"""Step 2: the agent's tools: web search, calculator, local file reader."""
import ast
import math
import operator
import time
from pathlib import Path

from ddgs import DDGS
from langchain_core.tools import tool

WORKSPACE = Path(__file__).parent / "workspace"
ALLOWED_SUFFIXES = {".txt", ".md", ".csv", ".json", ".log"}
MAX_FILE_CHARS = 6000

# ---------------------------------------------------------------- calculator
_BIN_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_FUNCS = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "log": math.log, "log10": math.log10, "exp": math.exp,
    "abs": abs, "round": round, "min": min, "max": max,
    "floor": math.floor, "ceil": math.ceil,
}
_CONSTS = {"pi": math.pi, "e": math.e}


def _eval(node):
    """Evaluate a parsed arithmetic expression. Anything else is rejected."""
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if (isinstance(node, ast.Constant) and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)):
        return node.value
    if isinstance(node, ast.Name) and node.id in _CONSTS:
        return _CONSTS[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("exponent too large")
        return _BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval(node.operand))
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in _FUNCS and not node.keywords):
        return _FUNCS[node.func.id](*[_eval(a) for a in node.args])
    raise ValueError("unsupported expression")


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression and return the numeric result.
    Use this for ANY arithmetic instead of calculating in your head.
    Supports + - * / // % **, parentheses, and the functions sqrt, sin, cos, tan,
    log, log10, exp, abs, round, min, max, floor, ceil, plus constants pi and e.
    Example input: '12500 / 5' or 'sqrt(144) + 2**3'."""
    try:
        result = _eval(ast.parse(expression.strip(), mode="eval"))
    except ZeroDivisionError:
        return "Error: division by zero."
    except Exception as e:
        return f"Error: could not evaluate '{expression}' ({e}). Use plain arithmetic only."
    if isinstance(result, float):
        result = round(result, 10)
    return str(result)


# --------------------------------------------------------------- file reader
def _available_files():
    if not WORKSPACE.exists():
        return []
    return sorted(p.name for p in WORKSPACE.iterdir() if p.is_file())


@tool
def list_files() -> str:
    """List the files available in the local workspace folder.
    Use this first if you are not sure which file names exist."""
    files = _available_files()
    return "Files in workspace: " + ", ".join(files) if files else "The workspace folder is empty."


@tool
def read_file(filename: str) -> str:
    """Read a local text file (.txt, .md, .csv, .json, .log) from the workspace folder
    and return its contents. Pass just the file name, for example 'project_notes.txt'."""
    try:
        path = (WORKSPACE / filename).resolve()
        if not path.is_relative_to(WORKSPACE.resolve()):
            return "Error: access denied. Only files inside the workspace folder can be read."
        if not path.is_file():
            return f"Error: file '{filename}' not found. Available files: {', '.join(_available_files()) or 'none'}"
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            return f"Error: unsupported file type '{path.suffix}'. Allowed: {', '.join(sorted(ALLOWED_SUFFIXES))}"
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error: could not read '{filename}' ({e})."

    if len(text) > MAX_FILE_CHARS:
        text = text[:MAX_FILE_CHARS] + f"\n...[truncated, file has more than {MAX_FILE_CHARS} characters]"
    return text


# ---------------------------------------------------------------- web search
@tool
def web_search(query: str) -> str:
    """Search the web (DuckDuckGo) for current or factual information and return the
    top results with title, snippet and URL. Use this for anything that needs
    up-to-date or external knowledge, such as news, populations, prices or facts."""
    last_error = "no results"
    for attempt in range(3):  # the search library is flaky, so retry briefly
        try:
            results = DDGS().text(query, max_results=5)
            if results:
                lines = []
                for i, r in enumerate(results, 1):
                    lines.append(f"{i}. {r.get('title', '')}\n   {r.get('body', '')}\n   {r.get('href', '')}")
                return "\n".join(lines)
        except Exception as e:
            last_error = str(e)
        time.sleep(1.5)
    return (
        f"Error: web search returned nothing for '{query}' ({last_error}). "
        "Do not repeat the same search. Use information you already have, try ONE "
        "differently worded query, or tell the user it could not be found."
    )


TOOLS = [web_search, calculator, read_file, list_files]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}