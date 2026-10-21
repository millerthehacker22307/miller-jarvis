#!/usr/bin/env python3
"""Miller's Jarvis — the app window.

A proper graphical chat app (no terminal, no commands to type):
open it, chat in the box, Jarvis replies in bubbles. On the right it shows
live pending tasks and what Jarvis remembers. Scheduled tasks fire in the
background and their results appear right in the chat.

Engine = brain.py + memory.py + scheduler.py + tools.py (all local).
"""
import queue
import threading
import tkinter as tk
from tkinter import scrolledtext

import brain
import jarvis as cli  # reuse the code-driven slash-command handler
import memory
import scheduler

BG = "#050810"
PANEL = "#0b1220"
CARD = "#0e1626"
MILLER_BUBBLE = "#0e3a5c"
JARVIS_BUBBLE = "#131c30"
TEXT = "#e2e8f0"
DIM = "#94a3b8"
ACCENT = "#38bdf8"
PINK = "#f0abfc"


class JarvisApp:
    def __init__(self, root):
        self.root = root
        self.cfg = brain.load_config()
        self.history = []
        self.events = queue.Queue()
        root.title("Miller's Jarvis — Personal Assistant")
        root.geometry("980x640")
        root.minsize(760, 520)
        root.configure(bg=BG)

        # ---------- header ----------
        head = tk.Frame(root, bg=PANEL, height=58)
        head.pack(fill="x")
        tk.Label(
            head, text="●  MILLER'S JARVIS", bg=PANEL, fg=ACCENT,
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left", padx=16, pady=12)
        self.status = tk.Label(
            head, text=f"Local model: {self.cfg['model']}  •  100% private  •  ₹0 cost",
            bg=PANEL, fg=DIM, font=("Segoe UI", 9),
        )
        self.status.pack(side="right", padx=16)

        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True)

        # ---------- chat side ----------
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)
        self.chat = scrolledtext.ScrolledText(
            left, wrap="word", bg=BG, fg=TEXT, insertbackground=TEXT,
            font=("Segoe UI", 11), bd=0, padx=14, pady=12, state="disabled",
        )
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_config("miller_name", foreground=ACCENT, font=("Segoe UI", 10, "bold"))
        self.chat.tag_config("jarvis_name", foreground=PINK, font=("Segoe UI", 10, "bold"))
        self.chat.tag_config("miller", background=MILLER_BUBBLE, foreground=TEXT)
        self.chat.tag_config("jarvis", background=JARVIS_BUBBLE, foreground=TEXT)
        self.chat.tag_config("sys", foreground=DIM, font=("Segoe UI", 9, "italic"))

        bar = tk.Frame(left, bg=PANEL)
        bar.pack(fill="x")
        self.entry = tk.Entry(
            bar, bg=CARD, fg=TEXT, insertbackground=TEXT, bd=0,
            font=("Segoe UI", 12),
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=12, pady=12, ipady=7)
        self.entry.bind("<Return>", lambda _e: self.send())
        self.entry.focus_set()
        tk.Button(
            bar, text="Send ➤", command=self.send, bg=ACCENT, fg="#082f49",
            activebackground="#7dd3fc", bd=0, font=("Segoe UI", 11, "bold"),
            padx=18, pady=7, cursor="hand2",
        ).pack(side="right", padx=12)

        # ---------- sidebar ----------
        side = tk.Frame(body, bg=PANEL, width=264)
        side.pack(side="right", fill="y")
        side.pack_propagate(False)
        tk.Label(side, text="⏰  Pending Tasks", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(14, 4))
        self.task_box = tk.Listbox(
            side, bg=CARD, fg=TEXT, bd=0, font=("Segoe UI", 9),
            activestyle="none", selectbackground="#1e3a5f", height=11,
        )
        self.task_box.pack(fill="x", padx=14)
        tk.Label(side, text="💾  Memory", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(16, 4))
        self.mem_label = tk.Label(
            side, text="", bg=PANEL, fg=DIM, font=("Segoe UI", 9),
            justify="left", wraplength=230,
        )
        self.mem_label.pack(anchor="w", padx=14)
        tk.Button(
            side, text="Show everything Jarvis remembers",
            command=lambda: self.say_system(self._facts_text()),
            bg=CARD, fg=ACCENT, activebackground="#16233c", bd=0,
            font=("Segoe UI", 9), padx=10, pady=6, cursor="hand2",
        ).pack(anchor="w", padx=14, pady=10)
        tk.Button(
            side, text="Refresh", command=self.refresh_sidebar,
            bg=CARD, fg=DIM, activebackground="#16233c", bd=0,
            font=("Segoe UI", 9), padx=10, pady=6, cursor="hand2",
        ).pack(anchor="w", padx=14)

        # ---------- start ----------
        self._bubble(
            "jarvis",
            "Namaste Miller! Main Jarvis — tumhara apna assistant. "
            "Mujhse kuch bhi pucho, koi date ya plan batao to main hamesha yaad rakhunga, "
            "aur time pe kaam bhi karke dunga. Neeche likho aur Send dabao.",
        )
        self.say_system("Tip: '/schedule 2026-10-22 07:00 Revise Cyber Security' jaisi commands bhi chalti hain — /help for all.")
        scheduler.start_background(announce=lambda msg: self.events.put(msg))
        self.refresh_sidebar()
        self.root.after(800, self._poll_events)

    # ---------- rendering ----------
    def _bubble(self, who, text):
        self.chat.configure(state="normal")
        if who == "miller":
            self.chat.insert("end", "You\n", "miller_name")
            self.chat.insert("end", f"  {text}  \n\n", "miller")
        else:
            self.chat.insert("end", "Jarvis\n", "jarvis_name")
            self.chat.insert("end", f"  {text}  \n\n", "jarvis")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def say_system(self, text):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{text}\n\n", "sys")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _facts_text(self):
        facts = memory.all_facts()
        if not facts:
            return "Abhi tak kuch yaad nahi hai."
        return "Ye sab yaad hai:\n" + "\n".join(f"• {f['text']}" for f in facts)

    def refresh_sidebar(self):
        self.task_box.delete(0, "end")
        pending = memory.list_tasks("pending")
        if not pending:
            self.task_box.insert("end", "  (no pending tasks)")
        for t in pending[:14]:
            self.task_box.insert("end", f"  {t['run_at']} — {t['text'][:30]}")
        count = len(memory.all_facts())
        self.mem_label.config(
            text=f"{count} fact(s) remembered.\nTasks aur facts laptop pe hi save hote hain."
        )

    # ---------- chat flow ----------
    def send(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self._bubble("miller", text)
        threading.Thread(target=self._answer, args=(text,), daemon=True).start()

    def _answer(self, text):
        reply = None
        if text.startswith("/"):
            try:
                reply = cli.handle_command(text)
            except SystemExit:  # /quit inside the GUI = close the window
                self.root.after(0, self.root.destroy)
                return
        if reply is None:
            try:
                reply = brain.ask(text, history=self.history, cfg=self.cfg)
            except Exception as exc:
                reply = (
                    "Model se connect nahi ho pa raha — Ollama band lag raha hai. "
                    "App band karke Start-Jarvis dobara chalao, wo Ollama start kar dega. "
                    f"(detail: {exc})"
                )
        self.events.put(("reply", reply))

    def _poll_events(self):
        try:
            while True:
                item = self.events.get_nowait()
                if isinstance(item, tuple) and item[0] == "reply":
                    self._bubble("jarvis", item[1])
                else:  # scheduler announcement
                    self.say_system(str(item))
                self.refresh_sidebar()
        except queue.Empty:
            pass
        self.root.after(800, self._poll_events)


def main():
    root = tk.Tk()
    JarvisApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
