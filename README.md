# Miller's Jarvis — Local Personal Assistant

A personal assistant that runs **entirely on your own laptop** — no cloud,
no API cost, no tokens, nothing leaves the machine. Built for an
8 GB RAM / no-GPU laptop.

It works the way a big assistant does, in miniature:

- **Brain** — a local open model served by [Ollama](https://ollama.com)
  (default `qwen3.5:4b`, chosen to fit 8 GB RAM on CPU), prompted to reason
  step by step before answering.
- **Memory** — facts, tasks and history are saved in `data/memory.json`
  and injected into every conversation, so it genuinely remembers across
  restarts (what you told it, your dates, your plans).
- **Scheduler** — background thread fires tasks at their time: simple
  reminders, daily repeats, or *agent tasks* where Jarvis does the work
  (prepare a summary, make notes) and saves the result in `data/results/`.
- **Tools** — calculator (safe, no `eval`), clock, notes, web page reader,
  remember/schedule/list-tasks.

## The app (recommended — no terminal, no commands)

Miller's Jarvis is a proper graphical app: a chat window with bubbles, a
live sidebar showing pending tasks and memory, and scheduled-task results
appearing right in the chat.

**Just double-click `Start-Jarvis.bat`** (Windows) or run
`bash start-jarvis.sh` (Linux/Mac). The launcher does everything itself:
finds Python, installs/starts Ollama if needed, downloads the model on the
first run, and opens the app window. If Python is missing it opens the
Python download page for you — install it with "Add to PATH" ticked, then
double-click again.

## Setup (one time, ~10 minutes)

**Windows:** install Python 3 (python.org, tick "Add to PATH") and Ollama
(ollama.com/download), then run `setup_windows.bat` — or simply use the
one-click launcher above, which guides you through both.

**Linux / WSL2:** run `bash setup_linux.sh`.

**Mac:** install Ollama, then `ollama pull qwen3.5:4b`.

## Run

Easiest: double-click **`Start-Jarvis.bat`**. From a terminal, the GUI is
`python app.py` and the text version is `python jarvis.py`.

## Everyday use

Just chat, in English / Hindi / Hinglish:

- "Mera Cyber Security paper 22 Oct ko hai, yaad rakh lo"
- "Kal subah 7 baje mujhe yaad dilana ki DBMS revise karna hai"
- "137 * 42 kitna hota hai? Step by step batao"
- "Mere pending tasks dikhao"

Reliable built-in commands (handled in code, always work):

| Command | What it does |
|---|---|
| `/remember <fact>` | Save a fact forever |
| `/facts` | Show everything remembered |
| `/schedule 2026-10-22 07:00 <text>` | One-time reminder |
| `/agent 2026-10-22 07:00 <text>` | Jarvis does the work at that time |
| `/daily 07:00 <text>` | Daily reminder |
| `/tasks` | List pending tasks |
| `/done <id>` | Mark a task done |
| `/forget <id>` | Delete a remembered fact |
| `/help` | All commands |

For always-on scheduling without keeping the chat open, point Windows Task
Scheduler / cron at: `python jarvis.py --check` (runs every due task once).

## Honest limits

A 4B local model is not a frontier cloud model: it is great at routine
reasoning, summaries, planning, reminders and memory, and weaker at very
hard problems. Speed on CPU is modest — fine for background scheduled work.
If chat feels slow, set `"model": "qwen3.5:2b"` in `config.json`.

## Privacy

Everything (model, memory, results) lives in this folder on your machine.
Delete `data/memory.json` to wipe its memory completely.
