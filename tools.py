"""Tools Jarvis can use. Stdlib only, deliberately small and safe."""
import ast
import datetime
import html
import os
import platform
import re
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
NOTES_DIR = os.path.join(BASE, "data", "notes")

# ---------------- calculator (safe AST eval, no eval()) ----------------

_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a ** b,
    ast.USub: lambda a: -a,
}


def calculator(expression):
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.operand))
        raise ValueError("unsupported expression")

    tree = ast.parse(str(expression), mode="eval")
    return _eval(tree)


# ---------------- clock ----------------

def now_text():
    return datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p")


# ---------------- notes (assistant's own notebook files) ----------------

def _note_path(name):
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", str(name)).strip("_") or "note"
    return os.path.join(NOTES_DIR, safe + ".txt")


def save_note(name, text):
    os.makedirs(NOTES_DIR, exist_ok=True)
    path = _note_path(name)
    with open(path, "a", encoding="utf-8") as f:
        f.write(str(text).rstrip() + "\n")
    return f"note saved: {os.path.basename(path)}"


def read_note(name):
    path = _note_path(name)
    if not os.path.exists(path):
        return "no such note"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()[-4000:]


# ---------------- web fetch (read a page as plain text) ----------------

def fetch_page(url, limit=3500):
    if not re.match(r"^https?://", str(url)):
        return "error: only http/https URLs"
    req = urllib.request.Request(
        str(url), headers={"User-Agent": "Mozilla/5.0 (MillerJarvis)"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read(300_000).decode("utf-8", "ignore")
    text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", raw)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    return text[:limit] or "page had no readable text"


# ---------------- system ----------------

def system_info():
    return (
        f"{platform.system()} {platform.release()}, "
        f"Python {platform.python_version()}, CPU cores: {os.cpu_count()}"
    )


TOOL_FUNCS = {
    "calculator": lambda args: calculator(args.get("expression", "")),
    "current_time": lambda args: now_text(),
    "save_note": lambda args: save_note(args.get("name", "notes"), args.get("text", "")),
    "read_note": lambda args: read_note(args.get("name", "notes")),
    "fetch_page": lambda args: fetch_page(args.get("url", "")),
    "system_info": lambda args: system_info(),
}

TOOL_DOCS = """Tools you may call (one per reply, exact JSON block):
{"tool": "calculator", "args": {"expression": "137 * 42"}}
{"tool": "current_time", "args": {}}
{"tool": "save_note", "args": {"name": "exam", "text": "DSA paper on 27 Oct"}}
{"tool": "read_note", "args": {"name": "exam"}}
{"tool": "fetch_page", "args": {"url": "https://example.com"}}
{"tool": "remember", "args": {"fact": "Miller's exam starts 22 Oct"}}
{"tool": "schedule", "args": {"text": "Revise DBMS Unit 2", "run_at": "2026-10-22 07:00", "repeat": "none", "kind": "remind"}}
{"tool": "list_tasks", "args": {}}
To call a tool, reply with ONLY that JSON block and nothing else.
When you get the tool result, continue reasoning and finish with a normal reply."""
