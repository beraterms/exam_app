from __future__ import annotations

import random
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .models import Question
from .storage import QuestionRepository


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT_DIR / "data" / "questions.json"
OPTION_LABELS = ("A", "B", "C", "D")
COURSE_NAME = "Siber Guvenlige Giris"
COLORS = {
    "bg": "#f5f6f8",
    "surface": "#ffffff",
    "surface_alt": "#eef1f4",
    "card": "#ffffff",
    "line": "#e1e5ea",
    "accent": "#1e88e5",
    "accent_dark": "#1565c0",
    "accent_soft": "#e3f2fd",
    "text": "#121417",
    "muted": "#5f6b7a",
    "success_bg": "#dff7e3",
    "success_fg": "#146c43",
    "danger_bg": "#ffe0e0",
    "danger_fg": "#b3261e",
    "neutral_bg": "#f3f5f7",
    "option_bg": "#e7f1ff",
    "table_alt": "#f7f8fa",
}


class QuestionBankApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"{COURSE_NAME} - Soru Bankasi")
        self.root.geometry("1180x780")
        self.root.minsize(980, 700)
        self.root.configure(bg=COLORS["bg"])

        self.repository = QuestionRepository(DATA_FILE)
        self.questions = self.repository.load_questions()
        self.tree_question_map: dict[str, Question] = {}
        self.add_correct_answer = tk.StringVar(value="A")
        self.solved_questions: set[tuple] = set()
        self.notebook: ttk.Notebook | None = None
        self.home_progress_label: ttk.Label | None = None
        self.home_total_label: ttk.Label | None = None

        self.session_window: tk.Toplevel | None = None
        self.session_start_time: float | None = None
        self.session_timer_job: str | None = None
        self.session_questions: list[Question] = []
        self.session_answers: list[int | None] = []
        self.session_correct: list[bool | None] = []
        self.session_index = 0
        self.session_correct_count = 0
        self.session_wrong_count = 0
        self.session_size = 40
        self.last_session_keys: set[tuple] = set()
        self.session_completed = False

        self.session_question_text: tk.Text | None = None
        self.session_option_buttons: list[tk.Button] = []
        self.session_progress_label: tk.Label | None = None
        self.session_counts_label: tk.Label | None = None
        self.session_timer_label: tk.Label | None = None
        self.session_result_label: tk.Label | None = None
        self.session_explanation_label: tk.Label | None = None
        self.session_prev_button: tk.Button | None = None
        self.session_next_button: tk.Button | None = None

        self._configure_styles()
        self._build_ui()
        self.refresh_question_list()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure(".", background=COLORS["bg"], foreground=COLORS["text"], font=("Segoe UI", 10))
        style.configure("App.TFrame", background=COLORS["bg"])
        style.configure("Surface.TFrame", background=COLORS["surface"])
        style.configure("Card.TFrame", background=COLORS["card"])

        style.configure("App.TNotebook", background=COLORS["bg"], borderwidth=0, tabmargins=(0, 6, 0, 0))
        style.configure(
            "App.TNotebook.Tab",
            background=COLORS["surface_alt"],
            foreground=COLORS["muted"],
            padding=(16, 8),
            borderwidth=0,
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "App.TNotebook.Tab",
            background=[("selected", COLORS["card"]), ("active", COLORS["surface_alt"])],
            foreground=[("selected", COLORS["text"]), ("active", COLORS["text"])],
        )

        style.configure("HeroTitle.TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Bahnschrift", 22, "bold"))
        style.configure("HeroBody.TLabel", background=COLORS["bg"], foreground=COLORS["muted"], font=("Segoe UI", 10))
        style.configure("SectionTitle.TLabel", background=COLORS["surface"], foreground=COLORS["text"], font=("Bahnschrift", 15, "bold"))
        style.configure("SectionBody.TLabel", background=COLORS["surface"], foreground=COLORS["muted"], font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=COLORS["card"], foreground=COLORS["text"], font=("Bahnschrift", 14, "bold"))
        style.configure("CardBody.TLabel", background=COLORS["card"], foreground=COLORS["muted"], font=("Segoe UI", 10))
        style.configure("Metric.TLabel", background=COLORS["card"], foreground=COLORS["accent_dark"], font=("Segoe UI Semibold", 10))
        style.configure("Status.TLabel", background=COLORS["surface"], foreground=COLORS["muted"], font=("Segoe UI Semibold", 10))
        style.configure("Field.TLabel", background=COLORS["surface"], foreground=COLORS["text"], font=("Segoe UI Semibold", 10))

        style.configure(
            "Primary.TButton",
            background=COLORS["accent"],
            foreground="#fffaf6",
            borderwidth=0,
            focusthickness=0,
            padding=(14, 10),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#3b6ef3"), ("pressed", COLORS["accent_dark"])],
        )
        style.configure(
            "Secondary.TButton",
            background=COLORS["surface_alt"],
            foreground=COLORS["accent_dark"],
            borderwidth=0,
            focusthickness=0,
            padding=(14, 10),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#e7ebf3"), ("pressed", "#d8deea")],
        )

        style.configure(
            "App.TEntry",
            fieldbackground=COLORS["card"],
            foreground=COLORS["text"],
            bordercolor=COLORS["line"],
            lightcolor=COLORS["line"],
            darkcolor=COLORS["line"],
            insertcolor=COLORS["text"],
            padding=8,
        )
        style.configure(
            "App.TCombobox",
            fieldbackground=COLORS["card"],
            foreground=COLORS["text"],
            bordercolor=COLORS["line"],
            lightcolor=COLORS["line"],
            darkcolor=COLORS["line"],
            arrowsize=15,
            padding=6,
        )
        style.map(
            "App.TCombobox",
            fieldbackground=[("readonly", COLORS["card"])],
            selectbackground=[("readonly", COLORS["card"])],
            selectforeground=[("readonly", COLORS["text"])],
        )

        style.configure(
            "App.Treeview",
            background=COLORS["card"],
            fieldbackground=COLORS["card"],
            foreground=COLORS["text"],
            borderwidth=0,
            rowheight=34,
            font=("Segoe UI", 10),
        )
        style.configure(
            "App.Treeview.Heading",
            background=COLORS["surface_alt"],
            foreground=COLORS["accent_dark"],
            borderwidth=0,
            padding=(10, 10),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "App.Treeview",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", "#fffaf6")],
        )

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text=f"{COURSE_NAME} Soru Bankasi", style="HeroTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text=f"{COURSE_NAME} dersi icin hazirlanan soru havuzu.",
            style="HeroBody.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.notebook = ttk.Notebook(self.root, style="App.TNotebook")
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        self.home_tab = ttk.Frame(self.notebook, padding=18, style="Surface.TFrame")
        self.add_tab = ttk.Frame(self.notebook, padding=18, style="Surface.TFrame")
        self.list_tab = ttk.Frame(self.notebook, padding=18, style="Surface.TFrame")

        self.notebook.add(self.home_tab, text="Ana Sayfa")
        self.notebook.add(self.add_tab, text="Soru Ekle")
        self.notebook.add(self.list_tab, text="Soru Listesi")

        self._build_home_tab()
        self._build_add_tab()
        self._build_list_tab()

    def _build_home_tab(self) -> None:
        self.home_tab.columnconfigure(0, weight=3)
        self.home_tab.columnconfigure(1, weight=2, minsize=260)
        self.home_tab.rowconfigure(0, weight=1)

        hero = tk.Frame(self.home_tab, bg=COLORS["card"])
        hero.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        hero.columnconfigure(0, weight=1)

        ttk.Label(hero, text="Cozum Oturumuna Hazirlan", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", padx=24, pady=(20, 6))
        ttk.Label(
            hero,
            text="Oturumu baslat, sureyi takip et, aciklamalarla pekistir.",
            style="CardBody.TLabel",
            wraplength=560,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        stats = tk.Frame(hero, bg=COLORS["card"])
        stats.grid(row=2, column=0, sticky="ew", padx=24)
        stats.columnconfigure(1, weight=1)

        ttk.Label(stats, text="Cozulen", style="Field.TLabel").grid(row=0, column=0, sticky="w")
        self.home_progress_label = ttk.Label(stats, text="", style="Metric.TLabel")
        self.home_progress_label.grid(row=0, column=1, sticky="e")
        self.home_total_label = ttk.Label(stats, text="", style="CardBody.TLabel")
        self.home_total_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        ttk.Button(hero, text="Cozmeye Basla", command=self.start_study_session, style="Primary.TButton").grid(
            row=3, column=0, sticky="w", padx=24, pady=(20, 24)
        )

        side = tk.Frame(self.home_tab, bg=COLORS["surface"])
        side.grid(row=0, column=1, sticky="nsew")
        side.columnconfigure(0, weight=1)

        ttk.Label(side, text="Oturum Ozeti", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", padx=18, pady=(18, 6))
        ttk.Label(
            side,
            text="Cozum oturumunu istedigin zaman baslatabilir ve durdurabilirsin.",
            style="CardBody.TLabel",
            wraplength=240,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 10))
        ttk.Label(
            side,
            text="Dogru veya yanlis fark etmeksizin aciklamayi gorebilirsin.",
            style="CardBody.TLabel",
            wraplength=240,
            justify="left",
        ).grid(row=2, column=0, sticky="w", padx=18, pady=(0, 18))

    def start_study_session(self) -> None:
        self.questions = self.repository.load_questions()
        if not self.questions:
            messagebox.showwarning("Bilgi", "Soru havuzu bos. Once soru ekleyin.")
            return

        if self.session_window is not None and self.session_window.winfo_exists():
            restart = messagebox.askyesno("Oturum Acik", "Mevcut oturum acik. Yeni oturum baslatilsin mi?")
            if restart:
                self._reset_session()
            else:
                self.session_window.lift()
            return

        self._create_session_window()
        self._reset_session()

    def _create_session_window(self) -> None:
        self.session_window = tk.Toplevel(self.root)
        self.session_window.title("Cozum Oturumu")
        self.session_window.geometry("980x700")
        self.session_window.minsize(860, 620)
        self.session_window.configure(bg=COLORS["bg"])
        self.session_window.protocol("WM_DELETE_WINDOW", self._close_session_window)

        self.session_window.columnconfigure(0, weight=1)
        self.session_window.rowconfigure(1, weight=1)

        header = tk.Frame(self.session_window, bg=COLORS["bg"])
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        header.columnconfigure(1, weight=1)

        self.session_progress_label = tk.Label(
            header,
            text="Soru 1/40",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=("Bahnschrift", 14, "bold"),
        )
        self.session_progress_label.grid(row=0, column=0, sticky="w")

        self.session_counts_label = tk.Label(
            header,
            text="Dogru: 0  Yanlis: 0",
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=("Segoe UI", 10),
        )
        self.session_counts_label.grid(row=0, column=1, sticky="w", padx=(16, 0))

        self.session_timer_label = tk.Label(
            header,
            text="Sure: 0:00",
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=("Segoe UI", 10),
        )
        self.session_timer_label.grid(row=0, column=2, sticky="e")

        content = tk.Frame(self.session_window, bg=COLORS["surface"])
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)

        question_title = tk.Label(
            content,
            text="Soru Metni",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI Semibold", 10),
        )
        question_title.grid(row=0, column=0, sticky="w", padx=4, pady=(16, 6))

        self.session_question_text = tk.Text(
            content,
            wrap="word",
            font=("Bahnschrift", 16),
            state="disabled",
            relief="flat",
            bd=0,
            padx=6,
            pady=6,
            background=COLORS["surface"],
            foreground=COLORS["text"],
            insertbackground=COLORS["text"],
            highlightthickness=0,
        )
        self.session_question_text.grid(row=1, column=0, sticky="nsew", padx=4)

        options_shell = tk.Frame(content, bg=COLORS["surface"])
        options_shell.grid(row=2, column=0, sticky="ew", padx=4, pady=(16, 8))
        options_shell.columnconfigure(0, weight=1)

        self.session_option_buttons = []
        for index, label in enumerate(OPTION_LABELS):
            button = tk.Button(
                options_shell,
                text=f"{label}) ",
                anchor="w",
                justify="left",
                wraplength=760,
                padx=12,
                pady=12,
                bd=0,
                relief="flat",
                bg=COLORS["option_bg"],
                fg=COLORS["text"],
                activebackground=COLORS["accent_soft"],
                activeforeground=COLORS["text"],
                font=("Segoe UI", 11),
                command=lambda idx=index: self._on_option_selected(idx),
            )
            button.grid(row=index, column=0, sticky="ew", pady=6)
            self.session_option_buttons.append(button)

        self.session_result_label = tk.Label(
            content,
            text="Cevabini sec.",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI Semibold", 10),
        )
        self.session_result_label.grid(row=3, column=0, sticky="w", padx=4, pady=(8, 8))

        self.session_explanation_label = tk.Label(
            content,
            text="",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 10),
            wraplength=760,
            justify="left",
        )
        self.session_explanation_label.grid(row=4, column=0, sticky="w", padx=4, pady=(0, 10))

        nav = tk.Frame(content, bg=COLORS["surface"])
        nav.grid(row=5, column=0, sticky="ew", padx=4, pady=(6, 16))
        nav.columnconfigure(1, weight=1)

        self.session_prev_button = tk.Button(
            nav,
            text="Onceki Soru",
            command=self._go_prev_question,
            bd=0,
            relief="flat",
            bg=COLORS["surface_alt"],
            fg=COLORS["text"],
            activebackground=COLORS["line"],
            font=("Segoe UI Semibold", 10),
            padx=16,
            pady=8,
        )
        self.session_prev_button.grid(row=0, column=0, sticky="w")

        self.session_next_button = tk.Button(
            nav,
            text="Sonraki Soru",
            command=self._go_next_question,
            bd=0,
            relief="flat",
            bg=COLORS["accent"],
            fg="#ffffff",
            activebackground=COLORS["accent_dark"],
            activeforeground="#ffffff",
            font=("Segoe UI Semibold", 10),
            padx=16,
            pady=8,
        )
        self.session_next_button.grid(row=0, column=2, sticky="e")

    def _reset_session(self) -> None:
        if not self.questions:
            return

        self._select_session_questions()
        if not self.session_questions:
            messagebox.showwarning("Bilgi", "Soru havuzu bos. Once soru ekleyin.")
            return

        self.session_answers = [None] * len(self.session_questions)
        self.session_correct = [None] * len(self.session_questions)
        self.session_index = 0
        self.session_correct_count = 0
        self.session_wrong_count = 0
        self.session_completed = False

        self._start_session_timer()
        self._render_session_question()

    def _select_session_questions(self) -> None:
        total = len(self.questions)
        if total == 0:
            self.session_questions = []
            return

        target = min(self.session_size, total)
        pool = list(self.questions)
        if self.last_session_keys:
            fresh = [item for item in pool if self._question_key(item) not in self.last_session_keys]
            if len(fresh) >= target:
                pool = fresh
            else:
                used = [item for item in pool if self._question_key(item) in self.last_session_keys]
                pool = fresh + used

        random.shuffle(pool)
        self.session_questions = pool[:target]
        self.last_session_keys = {self._question_key(question) for question in self.session_questions}

    def _start_session_timer(self) -> None:
        if self.session_timer_job is not None:
            self.root.after_cancel(self.session_timer_job)
            self.session_timer_job = None

        self.session_start_time = time.monotonic()
        self._tick_session_timer()

    def _tick_session_timer(self) -> None:
        if self.session_start_time is None or self.session_timer_label is None or self.session_window is None:
            return

        elapsed = int(time.monotonic() - self.session_start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.session_timer_label.config(text=f"Sure: {minutes}:{seconds:02d}")
        self.session_timer_job = self.root.after(1000, self._tick_session_timer)

    def _render_session_question(self) -> None:
        if not self.session_questions or self.session_question_text is None:
            return

        question = self.session_questions[self.session_index]
        self._update_session_header()

        self.session_question_text.config(state="normal")
        self.session_question_text.delete("1.0", tk.END)
        self.session_question_text.insert("1.0", question.text)
        self.session_question_text.config(state="disabled")

        for index, button in enumerate(self.session_option_buttons):
            option_text = question.options[index] if index < len(question.options) else "-"
            button.config(
                text=f"{OPTION_LABELS[index]}) {option_text}",
                state="normal",
                bg=COLORS["option_bg"],
                fg=COLORS["text"],
            )

        selected = self.session_answers[self.session_index]
        if selected is None:
            self.session_result_label.config(text="Cevabini sec.", fg=COLORS["muted"])
            self._set_session_explanation("")
        else:
            self._apply_answer_colors(selected, question.correct_option, question)

        self._update_session_nav()

    def _apply_answer_colors(self, selected: int, correct_index: int, question: Question) -> None:
        for index, button in enumerate(self.session_option_buttons):
            if index == correct_index:
                button.config(bg=COLORS["success_bg"], fg=COLORS["success_fg"])
            elif index == selected:
                button.config(bg=COLORS["danger_bg"], fg=COLORS["danger_fg"])
            else:
                button.config(bg=COLORS["option_bg"], fg=COLORS["text"])
            button.config(state="disabled")

        if selected == correct_index:
            self.session_result_label.config(text="Dogru cevap.", fg=COLORS["success_fg"])
        else:
            self.session_result_label.config(text="Yanlis cevap.", fg=COLORS["danger_fg"])

        explanation = question.explanation.strip() if question.explanation else ""
        if not explanation:
            explanation = "Bu soru icin aciklama eklenmemis."
        self._set_session_explanation(explanation)

    def _set_session_explanation(self, text: str) -> None:
        if self.session_explanation_label is None:
            return
        self.session_explanation_label.config(text=text, fg=COLORS["muted"] if not text or "eklenmemis" in text else COLORS["text"])

    def _update_session_header(self) -> None:
        total = len(self.session_questions)
        current = self.session_index + 1
        if self.session_progress_label is not None:
            self.session_progress_label.config(text=f"Soru {current}/{total}")
        if self.session_counts_label is not None:
            self.session_counts_label.config(text=f"Dogru: {self.session_correct_count}  Yanlis: {self.session_wrong_count}")

    def _update_session_nav(self) -> None:
        if self.session_prev_button is not None:
            prev_state = "normal" if self.session_index > 0 else "disabled"
            self.session_prev_button.config(state=prev_state)

        if self.session_next_button is None:
            return

        answered = self.session_answers[self.session_index] is not None
        is_last = self.session_index == len(self.session_questions) - 1
        if self.session_completed and is_last:
            self.session_next_button.config(text="Test Tamamlandi", state="disabled")
            return

        if answered:
            self.session_next_button.config(
                text="Testi Bitir" if is_last else "Sonraki Soru",
                state="normal",
            )
        else:
            self.session_next_button.config(text="Sonraki Soru", state="disabled")

    def _on_option_selected(self, index: int) -> None:
        if not self.session_questions:
            return

        if self.session_answers[self.session_index] is not None:
            return

        question = self.session_questions[self.session_index]
        self.session_answers[self.session_index] = index
        is_correct = index == question.correct_option
        self.session_correct[self.session_index] = is_correct

        if is_correct:
            self.session_correct_count += 1
        else:
            self.session_wrong_count += 1

        self._apply_answer_colors(index, question.correct_option, question)
        self._mark_question_completed(question)
        self._update_session_header()
        self._update_session_nav()

    def _go_next_question(self) -> None:
        if not self.session_questions:
            return

        if self.session_answers[self.session_index] is None:
            messagebox.showwarning("Uyari", "Once bu soruyu cevaplamalisiniz.")
            return

        if self.session_index == len(self.session_questions) - 1:
            if not self.session_completed:
                self.session_completed = True
                if self.session_timer_job is not None:
                    self.root.after_cancel(self.session_timer_job)
                    self.session_timer_job = None
                self._update_session_nav()
                self._show_score_window()
            return

        self.session_index += 1
        self._render_session_question()

    def _go_prev_question(self) -> None:
        if not self.session_questions or self.session_index == 0:
            return
        self.session_index -= 1
        self._render_session_question()

    def _show_score_window(self) -> None:
        total = len(self.session_questions)
        if total == 0:
            return

        score = round((self.session_correct_count / total) * 100)
        score_window = tk.Toplevel(self.root)
        score_window.title("Puanlama")
        score_window.geometry("760x620")
        score_window.minsize(680, 520)
        score_window.configure(bg=COLORS["bg"])

        score_window.columnconfigure(0, weight=1)
        score_window.rowconfigure(2, weight=1)

        header = tk.Frame(score_window, bg=COLORS["bg"])
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        header.columnconfigure(1, weight=1)

        tk.Label(
            header,
            text="Test Sonucu",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=("Bahnschrift", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            header,
            text=f"Puan: {score}/100",
            bg=COLORS["bg"],
            fg=COLORS["accent_dark"],
            font=("Segoe UI Semibold", 12),
        ).grid(row=0, column=1, sticky="e")

        tk.Label(
            score_window,
            text=f"Dogru: {self.session_correct_count}  Yanlis: {self.session_wrong_count}",
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 8))

        body = tk.Frame(score_window, bg=COLORS["surface"])
        body.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 16))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        text = tk.Text(
            body,
            wrap="word",
            state="normal",
            font=("Segoe UI", 10),
            bg=COLORS["surface"],
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            padx=8,
            pady=8,
        )
        text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(body, orient="vertical", command=text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scrollbar.set)

        wrong_items = []
        for idx, question in enumerate(self.session_questions, start=1):
            selected = self.session_answers[idx - 1]
            if selected is None or selected == question.correct_option:
                continue
            wrong_items.append((idx, question, selected))

        if not wrong_items:
            text.insert("1.0", "Tum sorular dogru cevaplandi. Tebrikler!")
        else:
            for order, question, selected in wrong_items:
                selected_label = OPTION_LABELS[selected] if selected is not None else "-"
                correct_label = OPTION_LABELS[question.correct_option]
                correct_text = question.options[question.correct_option] if question.correct_option < len(question.options) else ""
                text.insert(tk.END, f"{order}) {question.text}\n")
                text.insert(tk.END, f"   Senin cevabin: {selected_label}\n")
                text.insert(tk.END, f"   Dogru cevap: {correct_label}) {correct_text}\n\n")

        text.config(state="disabled")

        close_btn = tk.Button(
            score_window,
            text="Kapat",
            command=score_window.destroy,
            bd=0,
            relief="flat",
            bg=COLORS["accent"],
            fg="#ffffff",
            activebackground=COLORS["accent_dark"],
            activeforeground="#ffffff",
            font=("Segoe UI Semibold", 10),
            padx=16,
            pady=8,
        )
        close_btn.grid(row=3, column=0, sticky="e", padx=20, pady=(0, 16))

    def _close_session_window(self) -> None:
        if self.session_timer_job is not None:
            self.root.after_cancel(self.session_timer_job)
            self.session_timer_job = None
        self.session_start_time = None
        if self.session_window is not None:
            self.session_window.destroy()
        self.session_window = None

    def _build_add_tab(self) -> None:
        self.add_tab.columnconfigure(0, weight=1)

        shell = tk.Frame(self.add_tab, bg=COLORS["surface"], highlightthickness=0)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=1)

        ttk.Label(shell, text="Yeni Soru Ekle", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", padx=2, pady=(0, 4))
        ttk.Label(shell, text="Form basit tutuldu. Hedef hizli soru eklemek.", style="CardBody.TLabel").grid(
            row=1, column=0, sticky="w", padx=2, pady=(0, 16)
        )

        form = ttk.Frame(shell, style="Surface.TFrame")
        form.grid(row=2, column=0, sticky="nsew", padx=2, pady=(0, 16))
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Soru", style="Field.TLabel").grid(row=0, column=0, sticky="nw", pady=8, padx=(0, 16))
        self.question_entry = self._build_textbox(form, height=8)
        self.question_entry.grid(row=0, column=1, sticky="ew", pady=8)

        self.option_entries = []
        for index, label in enumerate(OPTION_LABELS, start=1):
            ttk.Label(form, text=f"Secenek {label}", style="Field.TLabel").grid(row=index, column=0, sticky="w", pady=8, padx=(0, 16))
            entry = ttk.Entry(form, style="App.TEntry")
            entry.grid(row=index, column=1, sticky="ew", pady=8)
            self.option_entries.append(entry)

        ttk.Label(form, text="Dogru Cevap", style="Field.TLabel").grid(row=5, column=0, sticky="w", pady=8, padx=(0, 16))
        answer_combo = ttk.Combobox(
            form,
            textvariable=self.add_correct_answer,
            values=list(OPTION_LABELS),
            state="readonly",
            width=12,
            style="App.TCombobox",
        )
        answer_combo.grid(row=5, column=1, sticky="w", pady=8)

        ttk.Label(form, text="Aciklama", style="Field.TLabel").grid(row=6, column=0, sticky="nw", pady=8, padx=(0, 16))
        self.explanation_entry = self._build_textbox(form, height=5)
        self.explanation_entry.grid(row=6, column=1, sticky="ew", pady=8)

        buttons = ttk.Frame(form, style="Card.TFrame")
        buttons.grid(row=7, column=1, sticky="w", pady=(16, 0))
        ttk.Button(buttons, text="Soruyu Kaydet", command=self.save_question, style="Primary.TButton").grid(row=0, column=0, padx=(0, 10))
        ttk.Button(buttons, text="Formu Temizle", command=self.clear_form, style="Secondary.TButton").grid(row=0, column=1)

        self.add_status = ttk.Label(shell, text="", style="Status.TLabel")
        self.add_status.grid(row=3, column=0, sticky="w", padx=2, pady=(0, 8))

    def _build_list_tab(self) -> None:
        self.list_tab.columnconfigure(0, weight=1)
        self.list_tab.rowconfigure(1, weight=1)

        top = tk.Frame(self.list_tab, bg=COLORS["surface"], highlightthickness=0)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Soru Listesi", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", padx=2, pady=(0, 4))
        ttk.Label(top, text="Kayitli sorular burada. Silme islemi bu ekrandan yapilir.", style="CardBody.TLabel").grid(
            row=1, column=0, sticky="w", padx=2, pady=(0, 12)
        )
        self.list_info_label = ttk.Label(top, text="", style="Metric.TLabel")
        self.list_info_label.grid(row=0, column=1, sticky="e", padx=2, pady=(0, 4))

        table_shell = tk.Frame(self.list_tab, bg=COLORS["surface"], highlightthickness=0)
        table_shell.grid(row=1, column=0, sticky="nsew")
        table_shell.columnconfigure(0, weight=1)
        table_shell.rowconfigure(0, weight=1)

        columns = ("question", "correct")
        self.question_tree = ttk.Treeview(table_shell, columns=columns, show="headings", style="App.Treeview")
        self.question_tree.grid(row=0, column=0, sticky="nsew", padx=(0, 0), pady=8)
        self.question_tree.heading("question", text="Soru")
        self.question_tree.heading("correct", text="Dogru")
        self.question_tree.column("question", width=820, anchor="w")
        self.question_tree.column("correct", width=110, anchor="center")
        self.question_tree.tag_configure("odd", background=COLORS["card"])
        self.question_tree.tag_configure("even", background=COLORS["table_alt"])

        scrollbar = ttk.Scrollbar(table_shell, orient="vertical", command=self.question_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(8, 0), pady=8)
        self.question_tree.configure(yscrollcommand=scrollbar.set)

        actions = ttk.Frame(self.list_tab, style="Surface.TFrame")
        actions.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        actions.columnconfigure(1, weight=1)
        ttk.Button(actions, text="Secili Soruyu Sil", command=self.delete_selected_question, style="Secondary.TButton").grid(
            row=0, column=0, sticky="w"
        )
        self.list_status_label = ttk.Label(actions, text="", style="Status.TLabel")
        self.list_status_label.grid(row=0, column=1, sticky="w", padx=(14, 0))

    def _build_textbox(self, parent: tk.Widget, height: int) -> tk.Text:
        return tk.Text(
            parent,
            height=height,
            wrap="word",
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
            padx=12,
            pady=10,
            background=COLORS["card"],
            foreground=COLORS["text"],
            insertbackground=COLORS["text"],
            highlightthickness=1,
            highlightbackground=COLORS["line"],
            highlightcolor=COLORS["accent"],
        )

    def _question_key(self, question: Question) -> tuple:
        return (question.text, tuple(question.options), question.correct_option)

    def _sync_solved_questions(self) -> None:
        current_keys = {self._question_key(question) for question in self.questions}
        self.solved_questions.intersection_update(current_keys)

    def refresh_question_list(self) -> None:
        self.questions = self.repository.load_questions()
        self.tree_question_map.clear()

        for item in self.question_tree.get_children():
            self.question_tree.delete(item)

        for index, question in enumerate(self.questions):
            question_preview = question.text.replace("\n", " ")
            if len(question_preview) > 105:
                question_preview = f"{question_preview[:102]}..."

            item_id = self.question_tree.insert(
                "",
                "end",
                values=(
                    question_preview,
                    OPTION_LABELS[question.correct_option] if 0 <= question.correct_option < len(OPTION_LABELS) else "?",
                ),
                tags=("even" if index % 2 == 0 else "odd",),
            )
            self.tree_question_map[item_id] = question

        total = len(self.questions)
        self.list_info_label.config(text=f"Toplam {total} soru")
        self._sync_solved_questions()
        self._update_progress_labels()

    def _update_progress_labels(self) -> None:
        total = len(self.questions)
        solved = len(self.solved_questions)
        progress_text = f"{solved}/{total}"
        if self.home_progress_label is not None:
            self.home_progress_label.config(text=progress_text)
        if self.home_total_label is not None:
            self.home_total_label.config(text=f"Toplam Soru: {total}")

    def _mark_question_completed(self, question: Question) -> None:
        question_key = self._question_key(question)
        if question_key in self.solved_questions:
            return
        self.solved_questions.add(question_key)
        self._update_progress_labels()

    def save_question(self) -> None:
        question_text = self.question_entry.get("1.0", tk.END).strip()
        options = [entry.get().strip() for entry in self.option_entries]
        explanation = self.explanation_entry.get("1.0", tk.END).strip()
        correct_option = OPTION_LABELS.index(self.add_correct_answer.get())

        if not question_text:
            messagebox.showwarning("Eksik Bilgi", "Soru metni bos olamaz.")
            return
        if any(not option for option in options):
            messagebox.showwarning("Eksik Bilgi", "Tum secenekleri doldurun.")
            return

        question = Question(
            subject=COURSE_NAME,
            text=question_text,
            options=options,
            correct_option=correct_option,
            explanation=explanation,
        )
        self.repository.add_question(question)

        self.add_status.config(text="Soru kaydedildi.", foreground=COLORS["success_fg"])
        self.list_status_label.config(text="")
        self.clear_form(clear_status=False)
        self.refresh_question_list()

    def delete_selected_question(self) -> None:
        selection = self.question_tree.selection()
        if not selection:
            messagebox.showwarning("Secim Gerekli", "Lutfen listeden bir soru secin.")
            return

        item_id = selection[0]
        question = self.tree_question_map.get(item_id)
        if question is None:
            messagebox.showerror("Hata", "Secilen soru bulunamadi.")
            return

        preview = question.text.replace("\n", " ")
        if len(preview) > 90:
            preview = f"{preview[:87]}..."

        confirmed = messagebox.askyesno("Soruyu Sil", f"Bu soruyu silmek istiyor musunuz?\n\n{preview}")
        if not confirmed:
            return

        deleted = self.repository.delete_question(question)
        if not deleted:
            messagebox.showerror("Hata", "Soru silinemedi.")
            return

        self.list_status_label.config(text="Secili soru silindi.", foreground=COLORS["danger_fg"])
        self.add_status.config(text="")
        self.refresh_question_list()

    def clear_form(self, clear_status: bool = True) -> None:
        self.question_entry.delete("1.0", tk.END)
        self.explanation_entry.delete("1.0", tk.END)
        self.add_correct_answer.set("A")
        for entry in self.option_entries:
            entry.delete(0, tk.END)

        if clear_status:
            self.add_status.config(text="")


def run_app() -> None:
    root = tk.Tk()
    QuestionBankApp(root)
    root.mainloop()
