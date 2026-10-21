"""The brain: talks to a local model through Ollama and runs the agent loop.

Design notes (why it works well even with a small 3-4B local model):
- A strong system prompt that forces step-by-step reasoning before answers.
- Memory is injected into every turn (relevant facts + pending tasks), so
  the assistant actually remembers instead of pretending to.
- Tools are called through a strict JSON-block protocol that small models
  follow reliably; core commands (/remember, /schedule...) are handled in
  code, not by the model, so they never fail.
"""
import json
import os
import re
import urllib.request

import memory
import tools

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE, "config.json")

DEFAULT_CONFIG = {
    "model": "qwen3.5:4b",          # fits 8 GB RAM, CPU-only
    "fallback_model": "qwen3.5:2b",  # use if the main model feels slow
    "ollama_url": "http://localhost:11434",
    "num_ctx": 4096,                 # small context = less RAM
    "temperature": 0.4,
    "owner_name": "Miller",
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    env_model = os.environ.get("JARVIS_MODEL")
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass
    if env_model:
        cfg["model"] = env_model
    return cfg


SYSTEM_PROMPT = """You are Jarvis, the personal assistant of {owner}.
You run fully on his own laptop. Be warm, brief and practical, like a smart friend.

HOW YOU WORK:
1. THINK step by step before answering: break the problem into parts, check
   each part, then give the final answer. Show the reasoning briefly for
   maths/logic questions, not for small talk.
2. REMEMBER: facts about {owner} are given to you below on every turn. Use
   them. When he tells you something worth keeping (dates, plans, names,
   preferences), call the "remember" tool so it is saved forever.
3. TASKS: when he asks you to do something later, call the "schedule" tool.
   "kind" is "remind" for a simple reminder, or "agent" when you must do
   actual work at that time (summarise, prepare notes, check something).
4. TOOLS: {tool_docs}
5. HONESTY: if you do not know something or a task is beyond you, say so
   plainly instead of inventing facts, numbers or dates.
6. LANGUAGE: reply in the same language he used (English / Hindi / Hinglish).

MEMORY (facts you remember about {owner}):
{facts}

PENDING TASKS:
{tasks}
"""


def _chat(cfg, messages):
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "stream": False,
        "options": {
            "num_ctx": cfg["num_ctx"],
            "temperature": cfg["temperature"],
        },
    }
    req = urllib.request.Request(
        cfg["ollama_url"].rstrip("/") + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("message", {}).get("content", "").strip()


def _system_text(cfg):
    facts = memory.relevant_facts("", limit=40)
    facts_text = "\n".join(f"- {f['text']}" for f in facts) or "- (nothing saved yet)"
    pending = memory.list_tasks("pending")
    tasks_text = (
        "\n".join(f"- [{t['run_at']}] {t['text']} ({t['kind']})" for t in pending[:15])
        or "- (no pending tasks)"
    )
    return SYSTEM_PROMPT.format(
        owner=cfg["owner_name"],
        tool_docs=tools.TOOL_DOCS,
        facts=facts_text,
        tasks=tasks_text,
    )


_TOOL_RE = re.compile(r"\{[\s\S]*\}")


def _extract_tool_call(text):
    """Return (tool_name, args) if the reply is a tool-call JSON block."""
    match = _TOOL_RE.search(text or "")
    if not match:
        return None
    try:
        obj = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if isinstance(obj, dict) and "tool" in obj:
        return obj["tool"], obj.get("args", {}) or {}
    return None


def _run_tool(name, args):
    if name == "remember":
        fact = memory.remember_fact(args.get("fact", ""), source="jarvis")
        return f"remembered: {fact['text']}" if fact else "nothing to remember"
    if name == "schedule":
        task = memory.add_task(
            args.get("text", ""),
            args.get("run_at", ""),
            repeat=args.get("repeat", "none"),
            kind=args.get("kind", "remind"),
        )
        return f"scheduled task #{task['id']} at {task['run_at']}: {task['text']}"
    if name == "list_tasks":
        pending = memory.list_tasks("pending")
        if not pending:
            return "no pending tasks"
        return "\n".join(f"[{t['run_at']}] {t['text']}" for t in pending)
    func = tools.TOOL_FUNCS.get(name)
    if func is None:
        return f"error: unknown tool {name}"
    try:
        return str(func(args))
    except Exception as exc:  # tools must never crash the loop
        return f"error: {exc}"


def ask(user_text, history=None, cfg=None):
    """One full agent turn. Returns the assistant's final reply text."""
    cfg = cfg or load_config()
    history = history if history is not None else []
    messages = [{"role": "system", "content": _system_text(cfg)}]
    messages += history[-8:]
    messages.append({"role": "user", "content": user_text})

    for _ in range(5):  # at most 5 tool steps per turn
        reply = _chat(cfg, messages)
        call = _extract_tool_call(reply)
        if call is None:
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": reply})
            memory.log_history("user", user_text)
            memory.log_history("jarvis", reply)
            return reply
        name, args = call
        result = _run_tool(name, args)
        messages.append({"role": "assistant", "content": reply})
        messages.append(
            {"role": "user", "content": f"Tool result for {name}: {result}\nNow continue and give your final reply."}
        )
    return "I tried a few steps but could not finish that. Please try asking in a simpler way."


def run_scheduled_task(task, cfg=None):
    """Used by the scheduler: Jarvis does the task and returns a result text."""
    prompt = (
        f"It is now time for this scheduled task: {task['text']}. "
        "Do the work properly, step by step, and give a clear final result. "
        "Save anything worth keeping with your tools."
    )
    return ask(prompt, history=[], cfg=cfg)
