"""Background scheduler: fires due tasks every 30 seconds.

- kind "remind": just a notification (printed + saved to results).
- kind "agent": Jarvis actually does the work via the local model and the
  result is saved under data/results/ and printed.
Daily tasks reschedule themselves for the next day after running.
"""
import datetime
import os
import threading
import time

import memory

RESULTS_DIR = os.path.join(memory.DATA_DIR, "results")
_stop = threading.Event()


def _now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def _save_result(task, text):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    path = os.path.join(RESULTS_DIR, f"{stamp}_{task['id']}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Task: {task['text']}\nWhen: {task['run_at']}\n\n{text}\n")
    return path


def fire_task(task, announce=print):
    """Run one due task and mark it done / reschedule if daily."""
    import brain  # local import: brain is heavy, scheduler alone stays light

    if task["kind"] == "agent":
        try:
            result = brain.run_scheduled_task(task)
        except Exception as exc:
            result = f"could not run (is Ollama running?): {exc}"
    else:
        result = f"Reminder: {task['text']}"
    path = _save_result(task, result)
    if task.get("repeat") == "daily":
        nxt = datetime.datetime.strptime(task["run_at"], "%Y-%m-%d %H:%M")
        nxt += datetime.timedelta(days=1)
        memory.update_task(
            task["id"],
            run_at=nxt.strftime("%Y-%m-%d %H:%M"),
            status="pending",
            result=result[:500],
        )
    else:
        memory.update_task(task["id"], status="done", result=result[:500])
    announce(f"\n*** Jarvis task fired: {task['text']}\n{result}\n(result saved: {path})\n")
    return result


def check_once(announce=print):
    fired = []
    for task in memory.due_tasks(_now_str()):
        fired.append(fire_task(task, announce=announce))
    return fired


def loop(announce=print):
    while not _stop.is_set():
        try:
            check_once(announce=announce)
        except Exception:
            pass  # a bad tick must never kill the scheduler
        _stop.wait(30)


def start_background(announce=print):
    thread = threading.Thread(target=loop, kwargs={"announce": announce}, daemon=True)
    thread.start()
    return thread


def stop():
    _stop.set()
