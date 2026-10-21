"""Persistent memory for Miller's Jarvis.

Stores facts, tasks and results as JSON on disk so the assistant
remembers across restarts. Zero dependencies (stdlib only).
"""
import json
import os
import threading
import time

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")
MEM_FILE = os.path.join(DATA_DIR, "memory.json")
_lock = threading.Lock()


def _load():
    if not os.path.exists(MEM_FILE):
        return {"facts": [], "tasks": [], "history": []}
    try:
        with open(MEM_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"facts": [], "tasks": [], "history": []}
    data.setdefault("facts", [])
    data.setdefault("tasks", [])
    data.setdefault("history", [])
    return data


def _save(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = MEM_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, MEM_FILE)


# ---------------- facts ----------------

def remember_fact(text, source="user"):
    """Save one durable fact. Returns the stored fact dict."""
    text = " ".join(str(text).split()).strip()
    if not text:
        return None
    with _lock:
        data = _load()
        for fact in data["facts"]:
            if fact["text"].lower() == text.lower():
                return fact
        fact = {
            "id": int(time.time() * 1000),
            "text": text,
            "source": source,
            "saved_at": time.strftime("%Y-%m-%d %H:%M"),
        }
        data["facts"].append(fact)
        _save(data)
        return fact


def all_facts():
    with _lock:
        return list(_load()["facts"])


def relevant_facts(query, limit=12):
    """Keyword-matched facts for prompt injection (simple, transparent)."""
    facts = all_facts()
    if not facts:
        return []
    words = {w.strip(".,?!").lower() for w in str(query).split() if len(w) > 2}
    scored = []
    for fact in facts:
        text = fact["text"].lower()
        score = sum(1 for w in words if w in text)
        scored.append((score, fact))
    scored.sort(key=lambda pair: (-pair[0], -pair[1]["id"]))
    picked = [fact for score, fact in scored if score > 0][:limit]
    if not picked:  # always give the newest few so the model has context
        picked = [fact for _, fact in scored[:5]]
    return picked


def forget_fact(fact_id):
    with _lock:
        data = _load()
        before = len(data["facts"])
        data["facts"] = [f for f in data["facts"] if f["id"] != fact_id]
        _save(data)
        return len(data["facts"]) < before


# ---------------- tasks ----------------

def add_task(text, run_at, repeat="none", kind="remind"):
    """run_at: local ISO string 'YYYY-MM-DD HH:MM'. repeat: none|daily."""
    with _lock:
        data = _load()
        task = {
            "id": int(time.time() * 1000),
            "text": text,
            "run_at": run_at,
            "repeat": repeat,
            "kind": kind,          # remind = just notify; agent = model does the work
            "status": "pending",
            "result": None,
        }
        data["tasks"].append(task)
        _save(data)
        return task


def list_tasks(status=None):
    with _lock:
        tasks = list(_load()["tasks"])
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    return sorted(tasks, key=lambda t: t["run_at"])


def update_task(task_id, **fields):
    with _lock:
        data = _load()
        for task in data["tasks"]:
            if task["id"] == task_id:
                task.update(fields)
                _save(data)
                return task
    return None


def due_tasks(now_str):
    return [t for t in list_tasks("pending") if t["run_at"] <= now_str]


# ---------------- history ----------------

def log_history(role, text):
    with _lock:
        data = _load()
        data["history"].append(
            {"at": time.strftime("%Y-%m-%d %H:%M"), "role": role, "text": str(text)[:2000]}
        )
        data["history"] = data["history"][-200:]
        _save(data)
