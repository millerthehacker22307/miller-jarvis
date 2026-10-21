#!/usr/bin/env python3
"""Miller's Jarvis — a local personal assistant.

Runs on his own laptop with a local model via Ollama: no cloud, no tokens,
nothing leaves the machine. It reasons step by step, remembers facts and
tasks forever (data/memory.json), and runs scheduled tasks in the
background (scheduler.py).

Usage:
    python jarvis.py            -> interactive chat (scheduler runs too)
    python jarvis.py --check    -> fire any due tasks once, then exit
                                   (for Windows Task Scheduler / cron)

Built-in commands (handled in code, they always work):
    /remember <fact>            save a fact forever
    /facts                      show everything remembered
    /schedule YYYY-MM-DD HH:MM <task text>     one-time reminder
    /agent YYYY-MM-DD HH:MM <task text>        Jarvis does the work then
    /daily HH:MM <task text>                   daily reminder
    /tasks                      list pending tasks
    /done <task id>             mark a task done
    /forget <fact id>           delete a remembered fact
    /quit
Anything else you type is a normal chat message to Jarvis.
"""
import datetime
import sys

import brain
import memory
import scheduler

HELP = __doc__


def _parse_when(rest):
    """Split 'YYYY-MM-DD HH:MM text' into (run_at, text)."""
    parts = rest.strip().split(" ", 2)
    if len(parts) < 3:
        return None, None
    return f"{parts[0]} {parts[1]}", parts[2]


def handle_command(text):
    """Returns a reply string if text was a command, else None."""
    low = text.lower()
    if low in ("/quit", "/exit", "quit", "exit"):
        scheduler.stop()
        print("Jarvis: Bye, Miller. Sab yaad rahega.")
        sys.exit(0)
    if low in ("/help", "help"):
        return HELP
    if low.startswith("/remember "):
        fact = memory.remember_fact(text[len("/remember "):], source="command")
        return f"Yaad kar liya: {fact['text']}" if fact else "Kuch samajh nahi aaya."
    if low == "/facts":
        facts = memory.all_facts()
        if not facts:
            return "Abhi tak kuch yaad nahi hai. /remember se batao."
        return "\n".join(f"[{f['id']}] {f['text']}" for f in facts)
    if low.startswith("/forget "):
        try:
            fid = int(text.split(" ", 1)[1])
        except (IndexError, ValueError):
            return "Use: /forget <fact id> (id /facts me dikhta hai)"
        return "Bhool gaya." if memory.forget_fact(fid) else "Wo id nahi mili."
    if low.startswith(("/schedule ", "/agent ", "/daily ")):
        kind = "agent" if low.startswith("/agent") else "remind"
        repeat = "daily" if low.startswith("/daily") else "none"
        rest = text.split(" ", 1)[1]
        if repeat == "daily":
            parts = rest.strip().split(" ", 1)
            if len(parts) < 2:
                return "Use: /daily HH:MM <task text>"
            today = datetime.date.today().isoformat()
            run_at, task_text = f"{today} {parts[0]}", parts[1]
            if run_at <= datetime.datetime.now().strftime("%Y-%m-%d %H:%M"):
                tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
                run_at = f"{tomorrow} {parts[0]}"
        else:
            run_at, task_text = _parse_when(rest)
            if not run_at:
                return "Use: /schedule YYYY-MM-DD HH:MM <task text>"
        task = memory.add_task(task_text, run_at, repeat=repeat, kind=kind)
        return f"Task set: [{run_at}] {task['text']} ({kind}{', daily' if repeat == 'daily' else ''})"
    if low == "/tasks":
        pending = memory.list_tasks("pending")
        if not pending:
            return "Koi pending task nahi hai."
        return "\n".join(
            f"[{t['id']}] {t['run_at']} — {t['text']} ({t['kind']})" for t in pending
        )
    if low.startswith("/done "):
        try:
            tid = int(text.split(" ", 1)[1])
        except (IndexError, ValueError):
            return "Use: /done <task id>"
        task = memory.update_task(tid, status="done")
        return "Task done mark ho gaya." if task else "Wo task id nahi mili."
    return None


def main():
    cfg = brain.load_config()
    if "--check" in sys.argv:
        scheduler.check_once()
        return
    print("=" * 56)
    print(f"  JARVIS — Miller's personal assistant (local, private)")
    print(f"  Model: {cfg['model']}  |  /help for commands")
    print("=" * 56)
    scheduler.start_background()
    history = []
    while True:
        try:
            user_text = input("\nMiller: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nJarvis: Bye, Miller.")
            break
        if not user_text:
            continue
        reply = handle_command(user_text)
        if reply is None:
            try:
                reply = brain.ask(user_text, history=history, cfg=cfg)
            except Exception as exc:
                reply = (
                    "Model se connect nahi ho pa raha. Kya Ollama chal raha hai? "
                    "Terminal me 'ollama serve' chalao, phir try karo. "
                    f"(detail: {exc})"
                )
        print(f"\nJarvis: {reply}")


if __name__ == "__main__":
    main()
