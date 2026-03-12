from __future__ import annotations

import io
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import tkinter as tk
from tkinter import messagebox, ttk

from .models import Question
from .storage import QuestionStore

try:
    import matplotlib
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from PIL import Image, ImageTk

    matplotlib.use("Agg")
    MATH_RENDER_AVAILABLE = True
except Exception:
    MATH_RENDER_AVAILABLE = False


COLORS = {
    "bg": "#0f1115",
    "surface": "#151922",
    "surface_alt": "#1c2230",
    "card": "#171b26",
    "line": "#2a3242",
    "accent": "#3a7afe",
    "accent_dark": "#2d64d8",
    "text": "#e6e9f0",
    "muted": "#9aa4b2",
    "success": "#22c55e",
    "danger": "#ef4444",
    "option": "#1b2230",
    "option_hover": "#233048",
}


@dataclass
class SessionState:
    questions: list[Question]
    answers: list[int | None]
    correct: list[bool | None]
    index: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    start_time: float | None = None
    timer_job: str | None = None


class MathRenderer:
    def __init__(self) -> None:
        self.cache: dict[str, tuple] = {}

    def render(self, latex: str) -> tk.PhotoImage | None:
        if not MATH_RENDER_AVAILABLE:
            return None
        if latex in self.cache:
            return self.cache[latex][1]  # Return PhotoImage from cache tuple
        try:
            # Clean up LaTeX for matplotlib compatibility
            # Matplotlib mathtext doesn't support \bmod, \pmod, \times, \equiv
            # Convert them to supported symbols/text
            import re
            clean_latex = latex
            clean_latex = re.sub(r'\\pmod\{([^}]*)\}', r'\\bmod \1', clean_latex)
            clean_latex = clean_latex.replace(r'\bmod', r'\ \mathrm{mod}\ ')
            clean_latex = clean_latex.replace(r'\times', r'\cdot')
            clean_latex = clean_latex.replace(r'\equiv', r'\ =\ ')
            
            fig = Figure(figsize=(0.01, 0.01), dpi=180)
            fig.patch.set_alpha(0.0)
            fig.text(0, 0, f"${clean_latex}$", fontsize=8, color=COLORS["text"])
            canvas = FigureCanvasAgg(fig)
            canvas.draw()
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=180, transparent=True, bbox_inches="tight", pad_inches=0.05)
            buf.seek(0)
            image = Image.open(buf)
            image.load()  # Load image data into memory before buffer is closed
            photo = ImageTk.PhotoImage(image)
            self.cache[latex] = (image, photo)  # Store both image and PhotoImage
            return photo
        except Exception as e:
            print(f"LaTeX render error: {latex} -> {e}")
            return None


class QuizApp:
    def __init__(self, root: tk.Tk, store: QuestionStore, session_size: int = 20) -> None:
        self.root = root
        self.store = store
        self.session_size = session_size
        self.math = MathRenderer()
        self.images: list[tk.PhotoImage] = []

        self.questions = self.store.load_questions()
        self.asked_ids = self.store.load_asked_ids()
        self.session: SessionState | None = None

        self.root.title("Kriptoloji - Soru Bankasi")
        self.root.geometry("1100x760")
        self.root.minsize(960, 680)
        self.root.configure(bg=COLORS["bg"])

        self._configure_styles()
        self._build_main()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure(".", background=COLORS["bg"], foreground=COLORS["text"], font=("Segoe UI", 10))
        style.configure("App.TFrame", background=COLORS["bg"])
        style.configure("Surface.TFrame", background=COLORS["surface"])
        style.configure("Card.TFrame", background=COLORS["card"])

        style.configure("Hero.TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Bahnschrift", 22, "bold"))
        style.configure("Body.TLabel", background=COLORS["bg"], foreground=COLORS["muted"], font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=COLORS["card"], foreground=COLORS["text"], font=("Bahnschrift", 14, "bold"))
        style.configure("CardBody.TLabel", background=COLORS["card"], foreground=COLORS["muted"], font=("Segoe UI", 10))

        style.configure(
            "Primary.TButton",
            background=COLORS["accent"],
            foreground="#ffffff",
            borderwidth=0,
            padding=(16, 10),
            font=("Segoe UI Semibold", 10),
        )
        style.map("Primary.TButton", background=[("active", COLORS["accent_dark"])])

        style.configure(
            "Secondary.TButton",
            background=COLORS["surface_alt"],
            foreground=COLORS["text"],
            borderwidth=0,
            padding=(14, 9),
            font=("Segoe UI Semibold", 10),
        )
        style.map("Secondary.TButton", background=[("active", COLORS["option_hover"])])

    def _build_main(self) -> None:
        shell = ttk.Frame(self.root, style="App.TFrame", padding=24)
        shell.pack(fill="both", expand=True)

        header = ttk.Frame(shell, style="App.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="Kriptoloji Soru Bankasi", style="Hero.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Kriptoloji sinavi icin hazirlanan soru havuzu ile pratik yap.",
            style="Body.TLabel",
        ).pack(anchor="w", pady=(4, 20))

        # --- Stats row ---
        total = len(self.questions)
        available = len([q for q in self.questions if q.qid and q.qid not in self.asked_ids])
        stats_row = tk.Frame(shell, bg=COLORS["bg"])
        stats_row.pack(fill="x", pady=(0, 16))
        for val, lbl in [
            (str(total), "Toplam Soru"),
            (str(available), "Cozulmemis"),
            (str(total - available), "Cozulen"),
        ]:
            card = tk.Frame(stats_row, bg=COLORS["card"], padx=20, pady=14)
            card.pack(side="left", padx=(0, 10))
            tk.Label(card, text=val, bg=COLORS["card"], fg=COLORS["accent"], font=("Bahnschrift", 22, "bold")).pack(anchor="w")
            tk.Label(card, text=lbl, bg=COLORS["card"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w")

        # --- Quiz card ---
        quiz_card = ttk.Frame(shell, style="Card.TFrame", padding=20)
        quiz_card.pack(fill="x", pady=(0, 12))
        ttk.Label(quiz_card, text="Soru Coz", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(
            quiz_card,
            text="Her oturumda 20 soru gelir. Secilen cevap geri alinamaz ve sonuc aninda gosterilir.",
            style="CardBody.TLabel",
            wraplength=820,
            justify="left",
        ).pack(anchor="w", pady=(6, 12))
        ttk.Button(quiz_card, text="Oturuma Basla", style="Primary.TButton", command=self.start_session).pack(anchor="w")

        # --- Tools card ---
        tools_card = ttk.Frame(shell, style="Card.TFrame", padding=20)
        tools_card.pack(fill="x")
        ttk.Label(tools_card, text="Hesap Makineleri", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(
            tools_card,
            text="RSA ve Diffie-Hellman protokolleri icin adim adim saglama hesabi yap.",
            style="CardBody.TLabel",
            wraplength=820,
            justify="left",
        ).pack(anchor="w", pady=(6, 12))
        btn_row = ttk.Frame(tools_card, style="Card.TFrame")
        btn_row.pack(anchor="w")
        ttk.Button(btn_row, text="RSA Hesaplayici", style="Secondary.TButton", command=self._open_rsa_window).pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="Diffie-Hellman", style="Secondary.TButton", command=self._open_dh_window).pack(side="left")

    def start_session(self) -> None:
        self.questions = self.store.load_questions()
        self.asked_ids = self.store.load_asked_ids()

        available = [q for q in self.questions if q.qid and q.qid not in self.asked_ids]
        if len(available) < self.session_size:
            messagebox.showwarning("Bilgi", "Yeni soru kalmadi veya yeterli soru yok.")
            return

        session_questions = random.sample(available, self.session_size)
        self.asked_ids.update(q.qid for q in session_questions)
        self.store.save_asked_ids(self.asked_ids)

        self.session = SessionState(
            questions=session_questions,
            answers=[None] * self.session_size,
            correct=[None] * self.session_size,
        )
        self._open_session_window()

    def _open_session_window(self) -> None:
        if self.session is None:
            return

        self.session_window = tk.Toplevel(self.root)
        self.session_window.title("Cozum Oturumu")
        self.session_window.geometry("1060x740")
        self.session_window.minsize(980, 680)
        self.session_window.configure(bg=COLORS["bg"])

        self.session_window.columnconfigure(0, weight=1)
        self.session_window.rowconfigure(1, weight=1)

        header = tk.Frame(self.session_window, bg=COLORS["bg"])
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        header.columnconfigure(1, weight=1)

        self.progress_label = tk.Label(header, text="Soru 1/20", bg=COLORS["bg"], fg=COLORS["text"], font=("Bahnschrift", 14, "bold"))
        self.progress_label.grid(row=0, column=0, sticky="w")

        self.counts_label = tk.Label(header, text="Dogru: 0  Yanlis: 0", bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 10))
        self.counts_label.grid(row=0, column=1, sticky="w", padx=(16, 0))

        self.timer_label = tk.Label(header, text="Sure: 0:00", bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 10))
        self.timer_label.grid(row=0, column=2, sticky="e")

        content = tk.Frame(self.session_window, bg=COLORS["surface"])
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        content.columnconfigure(0, weight=1)
        content.rowconfigure(2, weight=1)
        content.rowconfigure(4, weight=1)
        content.rowconfigure(5, weight=1)

        top_row = tk.Frame(content, bg=COLORS["surface"])
        top_row.grid(row=0, column=0, sticky="ew", padx=6, pady=(12, 6))
        top_row.columnconfigure(0, weight=1)

        self.meta_label = tk.Label(top_row, text="", bg=COLORS["surface"], fg=COLORS["muted"], font=("Segoe UI", 9))
        self.meta_label.pack(side="right")

        self.topic_label = tk.Label(top_row, text="", bg=COLORS["surface"], fg=COLORS["accent"], font=("Segoe UI Semibold", 10))
        self.topic_label.pack(side="left")

        self.question_text = tk.Text(
            content,
            wrap="word",
            font=("Bahnschrift", 13),
            state="disabled",
            relief="flat",
            bd=0,
            padx=6,
            pady=6,
            height=6,
            background=COLORS["surface"],
            foreground=COLORS["text"],
            highlightthickness=0,
        )
        self.question_text.tag_configure("normal", foreground=COLORS["text"], font=("Bahnschrift", 13))
        self.question_text.tag_configure("formula", foreground="#60a5fa", font=("Bahnschrift", 13, "bold"))
        self.question_text.tag_configure("number", foreground="#34d399", font=("Bahnschrift", 13))
        self.question_text.tag_configure("operator", foreground="#f87171", font=("Bahnschrift", 13, "bold"))
        self.question_text.grid(row=1, column=0, sticky="nsew", padx=6)
        self.question_scroll = ttk.Scrollbar(content, orient="vertical", command=self.question_text.yview)
        self.question_scroll.grid(row=1, column=1, sticky="ns")
        self.question_text.configure(yscrollcommand=self.question_scroll.set)

        options_shell = tk.Frame(content, bg=COLORS["surface"])
        options_shell.grid(row=2, column=0, sticky="nsew", padx=6, pady=(12, 6))
        options_shell.columnconfigure(0, weight=1)

        self.option_frames: list[tk.Frame] = []
        self.option_texts: list[tk.Text] = []
        for idx, label in enumerate(["A", "B", "C", "D"]):
            frame = tk.Frame(options_shell, bg=COLORS["option"], bd=0, highlightthickness=0)
            frame.grid(row=idx, column=0, sticky="ew", pady=5)
            frame.columnconfigure(0, weight=1)

            text_widget = tk.Text(
                frame,
                wrap="word",
                font=("Segoe UI", 11),
                state="disabled",
                relief="flat",
                bd=0,
                padx=12,
                pady=10,
                height=2,
                bg=COLORS["option"],
                fg=COLORS["text"],
                cursor="hand2",
                highlightthickness=0,
            )
            text_widget.pack(fill="both", expand=True)
            text_widget.tag_configure("normal", foreground=COLORS["text"], font=("Segoe UI", 11))
            text_widget.tag_configure("formula", foreground="#60a5fa", font=("Segoe UI", 11, "bold"))
            text_widget.tag_configure("number", foreground="#34d399", font=("Segoe UI", 11))
            text_widget.tag_configure("operator", foreground="#f87171", font=("Segoe UI", 11, "bold"))

            frame.bind("<Button-1>", lambda e, index=idx: self._select_answer(index))
            text_widget.bind("<Button-1>", lambda e, index=idx: self._select_answer(index))

            self.option_frames.append(frame)
            self.option_texts.append(text_widget)

        self.result_label = tk.Label(content, text="Cevabini sec.", bg=COLORS["surface"], fg=COLORS["muted"], font=("Segoe UI Semibold", 10))
        self.result_label.grid(row=3, column=0, sticky="w", padx=6, pady=(2, 4))

        self.tabs = ttk.Notebook(content)
        self.tabs.grid(row=4, column=0, sticky="nsew", padx=6, pady=(6, 0))

        self.solution_tab = ttk.Frame(self.tabs)
        self.hint_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.solution_tab, text="Cozum")
        self.tabs.add(self.hint_tab, text="Ipucu")
        
        # Make tabs expand with their container
        content.grid_rowconfigure(4, weight=1)
        
        # Configure solution tab grid
        self.solution_tab.grid_columnconfigure(0, weight=1)
        self.solution_tab.grid_rowconfigure(0, weight=1)

        self.solution_text = tk.Text(
            self.solution_tab,
            wrap="word",
            font=("Segoe UI", 10),
            bg=COLORS["surface"],
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            padx=8,
            pady=6,
            height=14,
            state="disabled",
        )
        self.solution_text.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.solution_scroll_y = ttk.Scrollbar(self.solution_tab, orient="vertical", command=self.solution_text.yview)
        self.solution_scroll_y.grid(row=0, column=1, sticky="ns")
        self.solution_text.configure(yscrollcommand=self.solution_scroll_y.set)

        # Configure solution text tags for coloring
        self.solution_text.tag_configure("normal", foreground=COLORS["text"], font=("Segoe UI", 10))
        self.solution_text.tag_configure("header", foreground="#fbbf24", font=("Segoe UI", 11, "bold"))
        self.solution_text.tag_configure("formula", foreground="#60a5fa", font=("Segoe UI", 10, "bold"))
        self.solution_text.tag_configure("number", foreground="#34d399")
        self.solution_text.tag_configure("operator", foreground="#f87171", font=("Segoe UI", 10, "bold"))

        self.hint_text = tk.Text(
            self.hint_tab,
            wrap="word",
            font=("Segoe UI", 10),
            bg=COLORS["surface"],
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            padx=8,
            pady=6,
            height=6,
            state="disabled",
        )
        self.hint_text.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.hint_scroll = ttk.Scrollbar(self.hint_tab, orient="vertical", command=self.hint_text.yview)
        self.hint_scroll.grid(row=0, column=1, sticky="ns")
        self.hint_text.configure(yscrollcommand=self.hint_scroll.set)
        
        # Configure hint tab grid
        self.hint_tab.grid_columnconfigure(0, weight=1)
        self.hint_tab.grid_rowconfigure(0, weight=1)

        nav = tk.Frame(content, bg=COLORS["surface"])
        nav.grid(row=5, column=0, sticky="ew", padx=6, pady=(8, 12))
        nav.columnconfigure(1, weight=1)

        tk.Button(nav, text="Onceki Soru", command=self._prev_question, bd=0, relief="flat", bg=COLORS["surface_alt"], fg=COLORS["text"], padx=16, pady=8).grid(row=0, column=0, sticky="w")
        tk.Button(nav, text="Sonraki Soru", command=self._next_question, bd=0, relief="flat", bg=COLORS["accent"], fg="#ffffff", padx=16, pady=8).grid(row=0, column=2, sticky="e")

        self.session.start_time = time.monotonic()
        self._tick_timer()
        self._render_question()

    def _tick_timer(self) -> None:
        if self.session is None or self.session.start_time is None:
            return
        elapsed = int(time.monotonic() - self.session.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.timer_label.config(text=f"Sure: {minutes}:{seconds:02d}")
        self.session.timer_job = self.session_window.after(1000, self._tick_timer)

    def _render_question(self) -> None:
        if self.session is None:
            return
        question = self.session.questions[self.session.index]
        self.progress_label.config(text=f"Soru {self.session.index + 1}/{self.session_size}")
        self.counts_label.config(text=f"Dogru: {self.session.correct_count}  Yanlis: {self.session.wrong_count}")
        parts = question.subject.split("/")
        topic = parts[-1].strip() if len(parts) > 1 else question.subject
        self.topic_label.config(text=f"● {topic}")
        self.meta_label.config(text=f"Kaynak: {question.source}  |  Zorluk: {question.difficulty}")

        self.images.clear()
        self._set_text(self.question_text, question.text)

        for idx, (frame, text_widget) in enumerate(zip(self.option_frames, self.option_texts)):
            frame.config(bg=COLORS["option"])
            text_widget.config(state="normal", bg=COLORS["option"])
            text_widget.delete("1.0", tk.END)
            option_text = f"{['A','B','C','D'][idx]}) {question.options[idx] if idx < len(question.options) else '-'}"
            self._insert_line_with_formulas(text_widget, option_text)
            text_widget.config(state="disabled")
            frame.bind("<Button-1>", lambda e, index=idx: self._select_answer(index))
            text_widget.bind("<Button-1>", lambda e, index=idx: self._select_answer(index))

        self.result_label.config(text="Cevabini sec.", fg=COLORS["muted"])
        self._set_text(self.solution_text, "Cevap secilince cozum gosterilir.")
        hint_content = question.formulas if question.formulas else []
        self._render_formulas(self.hint_text, hint_content, empty_message="Bu soru icin ipucu yok.")

        answer = self.session.answers[self.session.index]
        if answer is not None:
            self._apply_answer_state(answer)

    def _set_text(self, widget: tk.Text, content: str) -> None:
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        if not content:
            widget.insert("1.0", "-")
            widget.config(state="disabled")
            return
        # Support inline formulas with [[...]] delimiters
        self._insert_line_with_formulas(widget, content)
        widget.config(state="disabled")

    def _render_formulas(self, widget: tk.Text, formulas: list[str], empty_message: str) -> None:
        widget.config(state="normal")
        widget.delete("1.0", tk.END)

        if not formulas:
            widget.insert("1.0", empty_message)
            widget.config(state="disabled")
            return

        if not MATH_RENDER_AVAILABLE:
            widget.insert(tk.END, "\n".join(formulas))
            widget.config(state="disabled")
            return

        for line in formulas:
            latex = self._latexify(line)
            image = self.math.render(latex)
            if image is None:
                widget.insert(tk.END, line + "\n")
                continue
            self.images.append(image)
            widget.image_create(tk.END, image=image)
            widget.insert(tk.END, "\n")
        widget.config(state="disabled")

    def _latexify(self, line: str) -> str:
        replacements = {
            "φ": r"\varphi",
            "Φ": r"\Phi",
            "Π": r"\Pi",
            "π": r"\pi",
            "≡": r"\equiv",
            "≤": r"\leq",
            "≥": r"\geq",
        }
        for key, value in replacements.items():
            line = line.replace(key, value)
        line = line.replace("*", r"\cdot ")
        line = line.replace(" mod ", r"\bmod ")
        return line.strip()

    def _select_answer(self, index: int) -> None:
        if self.session is None:
            return
        if self.session.answers[self.session.index] is not None:
            return

        question = self.session.questions[self.session.index]
        self.session.answers[self.session.index] = index
        is_correct = index == question.correct_option
        self.session.correct[self.session.index] = is_correct

        if is_correct:
            self.session.correct_count += 1
            self.result_label.config(text="Dogru cevap.", fg=COLORS["success"])
        else:
            self.session.wrong_count += 1
            self.result_label.config(text="Yanlis cevap.", fg=COLORS["danger"])

        self._apply_answer_state(index)
        self._render_solution(question)

    def _apply_answer_state(self, selected: int) -> None:
        if self.session is None:
            return
        question = self.session.questions[self.session.index]
        for idx, (frame, text_widget) in enumerate(zip(self.option_frames, self.option_texts)):
            if idx == question.correct_option:
                bg = "#134e2a"
            elif idx == selected:
                bg = "#4b1c1c"
            else:
                bg = COLORS["option"]
            frame.config(bg=bg)
            text_widget.config(bg=bg)
            frame.unbind("<Button-1>")
            text_widget.unbind("<Button-1>")

    def _render_solution(self, question: Question) -> None:
        import re
        
        self.solution_text.config(state="normal")
        self.solution_text.delete("1.0", tk.END)
        self.solution_text.insert(
            "1.0",
            f"Dogru Cevap: {['A','B','C','D'][question.correct_option]}\n\n",
            "header",
        )

        # Process explanation line by line
        for line in question.explanation.splitlines():
            # Always use _insert_line_with_formulas for consistency
            # It handles both inline [[...]] formulas and plain text
            self._insert_line_with_formulas(self.solution_text, line + "\n")

        if question.formulas:
            self.solution_text.insert(tk.END, "\nFormul:\n", "header")
            if MATH_RENDER_AVAILABLE:
                for line in question.formulas:
                    latex = self._latexify(line)
                    image = self.math.render(latex)
                    if image is None:
                        self.solution_text.insert(tk.END, line + "\n", "formula")
                        continue
                    self.images.append(image)
                    self.solution_text.image_create(tk.END, image=image)
                    self.solution_text.insert(tk.END, "\n")
            else:
                for line in question.formulas:
                    self.solution_text.insert(tk.END, line + "\n", "formula")

        self.solution_text.config(state="disabled")

    def _looks_like_formula(self, line: str) -> bool:
        triggers = ["=", "≡", "^", "mod", "phi", "φ"]
        lowered = line.lower()
        return any(token in lowered for token in triggers)

    def _insert_line_with_formulas(self, widget: tk.Text, text: str) -> None:
        """Insert text with inline LaTeX formulas ([[...]]) rendered as images."""
        import re
        
        # Pattern to find [[...]] formulas - use non-greedy match
        formula_pattern = r'\[\[(.+?)\]\]'
        
        last_end = 0
        found_formulas = False
        
        for match in re.finditer(formula_pattern, text):
            found_formulas = True
            # Insert normal text before formula
            if match.start() > last_end:
                normal_part = text[last_end:match.start()]
                self._insert_colored_text(widget, normal_part)
            
            # Render and insert formula
            formula_content = match.group(1).strip()
            image = self.math.render(formula_content)
            if image is not None:
                self.images.append(image)
                widget.image_create(tk.END, image=image)
            else:
                # Fallback: show formula text if rendering fails
                widget.insert(tk.END, f"[[{formula_content}]]", "formula")
            
            last_end = match.end()
        
        # Insert remaining normal text
        if last_end < len(text):
            self._insert_colored_text(widget, text[last_end:])
    
    def _insert_colored_text(self, widget: tk.Text, text: str) -> None:
        """Insert text with colored mathematical symbols and operators."""
        import re
        
        # Pattern to match mathematical operators and expressions
        patterns = [
            (r"(=|≡|≤|≥|\^|mod)", "operator"),  # Mathematical operators
            (r"\b(\d+)\b", "number"),  # Numbers
        ]
        
        last_end = 0
        matches = []
        
        # Collect all matches with their tags
        for pattern, tag in patterns:
            for match in re.finditer(pattern, text):
                matches.append((match.start(), match.end(), match.group(), tag))
        
        # Sort matches by position
        matches.sort(key=lambda x: x[0])
        
        # Remove overlapping matches
        filtered_matches = []
        for match in matches:
            if not filtered_matches or match[0] >= filtered_matches[-1][1]:
                filtered_matches.append(match)
        
        # Insert text with appropriate tags
        last_end = 0
        for start, end, matched_text, tag in filtered_matches:
            if start > last_end:
                widget.insert(tk.END, text[last_end:start], "normal")
            widget.insert(tk.END, matched_text, tag)
            last_end = end
        
        # Insert remaining text with normal tag
        if last_end < len(text):
            widget.insert(tk.END, text[last_end:], "normal")

    def _next_question(self) -> None:
        if self.session is None:
            return
        if self.session.answers[self.session.index] is None:
            messagebox.showwarning("Uyari", "Once bu soruyu cevaplayin.")
            return
        if self.session.index >= self.session_size - 1:
            messagebox.showinfo("Oturum", "Oturum tamamlandi.")
            return
        self.session.index += 1
        self._render_question()

    def _prev_question(self) -> None:
        if self.session is None:
            return
        if self.session.index == 0:
            return
        self.session.index -= 1
        self._render_question()

    # ------------------------------------------------------------------ #
    #  Hesap Makineleri                                                    #
    # ------------------------------------------------------------------ #

    def _open_rsa_window(self) -> None:
        import math

        win = tk.Toplevel(self.root)
        win.title("RSA Hesaplayici")
        win.geometry("600x640")
        win.configure(bg=COLORS["bg"])
        win.resizable(False, False)

        shell = tk.Frame(win, bg=COLORS["bg"], padx=24, pady=20)
        shell.pack(fill="both", expand=True)

        tk.Label(shell, text="RSA Hesaplayici", bg=COLORS["bg"], fg=COLORS["text"], font=("Bahnschrift", 18, "bold")).pack(anchor="w")
        tk.Label(shell, text="Iki asal sayiyla RSA sifreleyip coz, sonuclari adim adim gor.", bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 16))

        form = tk.Frame(shell, bg=COLORS["bg"])
        form.pack(fill="x")
        entries = _calc_form(
            form,
            [("p  (asal)", "p"), ("q  (asal)", "q"), ("e  (0 = otomatik)", "e"), ("Mesaj M", "M")],
            COLORS["bg"], COLORS["muted"], COLORS["text"], COLORS["line"], COLORS["accent"],
        )

        out = _calc_output(shell, COLORS["surface"], COLORS["text"], height=12)

        def compute() -> None:
            try:
                p = int(entries["p"].get())
                q = int(entries["q"].get())
                e_val = int(entries["e"].get() or "0")
                M = int(entries["M"].get())
            except ValueError:
                messagebox.showerror("Hata", "Tum alanlar tam sayi olmalidir.", parent=win)
                return

            n = p * q
            phi = (p - 1) * (q - 1)

            if e_val == 0:
                e_val = 3
                while e_val < phi:
                    if math.gcd(e_val, phi) == 1:
                        break
                    e_val += 2

            if math.gcd(e_val, phi) != 1:
                messagebox.showerror("Hata", f"gcd(e={e_val}, phi(n)={phi}) = {math.gcd(e_val, phi)} ≠ 1\ne gecersiz.", parent=win)
                return

            try:
                d = pow(e_val, -1, phi)
            except Exception:
                messagebox.showerror("Hata", "d hesaplanamadi.", parent=win)
                return

            c = pow(M, e_val, n)
            f = pow(c, d, n)

            lines = [
                f"── Anahtar Uretimi ──────────────────────",
                f"  n   = p × q          = {p} × {q} = {n}",
                f"  φ(n)= (p-1)(q-1)    = {p-1} × {q-1} = {phi}",
                f"  e   = {e_val}",
                f"  d   = {d}",
                f"",
                f"── Sifreleme ────────────────────────────",
                f"  C = M^e mod n = {M}^{e_val} mod {n} = {c}",
                f"",
                f"── Cozme ────────────────────────────────",
                f"  M = C^d mod n = {c}^{d} mod {n} = {f}",
                f"",
                f"  {'✓ Dogrulandi! (M = f = ' + str(f) + ')' if M == f else '✗ Hata: M ≠ f'}",
            ]
            out.config(state="normal")
            out.delete("1.0", tk.END)
            out.insert("1.0", "\n".join(lines))
            out.config(state="disabled")

        tk.Button(
            shell, text="Hesapla", command=compute, bd=0, relief="flat",
            bg=COLORS["accent"], fg="#ffffff", font=("Segoe UI Semibold", 10),
            padx=20, pady=10, cursor="hand2",
        ).pack(anchor="w", pady=(16, 12))

        out.pack_forget()
        out.pack(fill="x")

    def _open_dh_window(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Diffie-Hellman Hesaplayici")
        win.geometry("600x580")
        win.configure(bg=COLORS["bg"])
        win.resizable(False, False)

        shell = tk.Frame(win, bg=COLORS["bg"], padx=24, pady=20)
        shell.pack(fill="both", expand=True)

        tk.Label(shell, text="Diffie-Hellman Anahtar Degisimi", bg=COLORS["bg"], fg=COLORS["text"], font=("Bahnschrift", 18, "bold")).pack(anchor="w")
        tk.Label(shell, text="p, g ve ozel anahtarlarla ortak gizli anahtarin nasil hesaplandığini gor.", bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 16))

        form = tk.Frame(shell, bg=COLORS["bg"])
        form.pack(fill="x")
        entries = _calc_form(
            form,
            [("p  (asal modül)", "p"), ("g  (üreteç)", "g"), ("a  (Alice özel anahtar)", "a"), ("b  (Bob özel anahtar)", "b")],
            COLORS["bg"], COLORS["muted"], COLORS["text"], COLORS["line"], COLORS["accent"],
        )

        out = _calc_output(shell, COLORS["surface"], COLORS["text"], height=11)

        def compute() -> None:
            try:
                p = int(entries["p"].get())
                g = int(entries["g"].get())
                a = int(entries["a"].get())
                b = int(entries["b"].get())
            except ValueError:
                messagebox.showerror("Hata", "Tum alanlar tam sayi olmalidir.", parent=win)
                return

            A = pow(g, a, p)
            B = pow(g, b, p)
            K1 = pow(B, a, p)
            K2 = pow(A, b, p)

            lines = [
                f"── Public Anahtarlar ────────────────────",
                f"  A = g^a mod p = {g}^{a} mod {p} = {A}   (Alice)",
                f"  B = g^b mod p = {g}^{b} mod {p} = {B}   (Bob)",
                f"",
                f"── Ortak Gizli Anahtar ──────────────────",
                f"  Alice: K = B^a mod p = {B}^{a} mod {p} = {K1}",
                f"  Bob:   K = A^b mod p = {A}^{b} mod {p} = {K2}",
                f"",
                f"  {'✓ Ortak anahtar olusturuldu: K = ' + str(K1) if K1 == K2 else '✗ Hata: K1 ≠ K2'}",
            ]
            out.config(state="normal")
            out.delete("1.0", tk.END)
            out.insert("1.0", "\n".join(lines))
            out.config(state="disabled")

        tk.Button(
            shell, text="Hesapla", command=compute, bd=0, relief="flat",
            bg=COLORS["accent"], fg="#ffffff", font=("Segoe UI Semibold", 10),
            padx=20, pady=10, cursor="hand2",
        ).pack(anchor="w", pady=(16, 12))

        out.pack_forget()
        out.pack(fill="x")


def _calc_form(parent: tk.Frame, fields: list[tuple[str, str]], bg: str, fg_muted: str, fg_text: str, line_color: str, accent: str) -> dict[str, tk.Entry]:
    """Build a labeled entry form and return {key: entry} dict."""
    entries: dict[str, tk.Entry] = {}
    for label, key in fields:
        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, bg=bg, fg=fg_muted, font=("Segoe UI", 10), width=22, anchor="w").pack(side="left")
        entry = tk.Entry(
            row,
            bg="#1c2230",
            fg=fg_text,
            insertbackground=fg_text,
            relief="flat",
            font=("Segoe UI", 11),
            bd=0,
            highlightthickness=1,
            highlightcolor=accent,
            highlightbackground=line_color,
        )
        entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(8, 0))
        entries[key] = entry
    return entries


def _calc_output(parent: tk.Frame, bg: str, fg: str, height: int = 10) -> tk.Text:
    t = tk.Text(
        parent,
        height=height,
        bg="#151922",
        fg=fg,
        relief="flat",
        bd=0,
        font=("Consolas", 10),
        padx=12,
        pady=10,
        state="disabled",
        highlightthickness=0,
    )
    t.pack(fill="x", pady=(0, 0))
    return t


def run_app() -> None:
    root = tk.Tk()
    data_dir = Path(__file__).resolve().parents[1] / "data"
    store = QuestionStore(data_dir / "questions.json", data_dir / "asked.json")
    app = QuizApp(root, store)
    root.mainloop()
