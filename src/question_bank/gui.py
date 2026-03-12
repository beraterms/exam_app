from __future__ import annotations

import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .models import Question
from .storage import QuestionRepository


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT_DIR / "data" / "questions.json"
OPTION_LABELS = ("A", "B", "C", "D")
COLORS = {
    "bg": "#f4f5f7",
    "surface": "#ffffff",
    "surface_alt": "#f0f2f5",
    "card": "#ffffff",
    "line": "#e3e6ea",
    "accent": "#2563eb",
    "accent_dark": "#1e40af",
    "accent_soft": "#dbe7ff",
    "text": "#111827",
    "muted": "#6b7280",
    "success_bg": "#dcfce7",
    "success_fg": "#166534",
    "danger_bg": "#fee2e2",
    "danger_fg": "#b91c1c",
    "neutral_bg": "#f8fafc",
    "table_alt": "#f9fafb",
}


class QuestionBankApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Soru Bankasi")
        self.root.geometry("1180x780")
        self.root.minsize(980, 700)
        self.root.configure(bg=COLORS["bg"])

        self.repository = QuestionRepository(DATA_FILE)
        self.questions = self.repository.load_questions()
        self.filtered_questions: list[Question] = []
        self.tree_question_map: dict[str, Question] = {}
        self.current_question: Question | None = None
        self.current_answer = tk.IntVar(value=-1)
        self.study_subject = tk.StringVar(value="Tum Dersler")
        self.add_correct_answer = tk.StringVar(value="A")

        self._configure_styles()
        self._build_ui()
        self.refresh_question_list()
        self.refresh_subject_filter()
        self.prepare_study_queue()

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

        ttk.Label(header, text="Soru Bankasi", style="HeroTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Calisma ekrani odakta. Sorular buyuk alanda, yonetim araclari yaninda.",
            style="HeroBody.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        notebook = ttk.Notebook(self.root, style="App.TNotebook")
        notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        self.study_tab = ttk.Frame(notebook, padding=18, style="Surface.TFrame")
        self.add_tab = ttk.Frame(notebook, padding=18, style="Surface.TFrame")
        self.list_tab = ttk.Frame(notebook, padding=18, style="Surface.TFrame")

        notebook.add(self.study_tab, text="Calis")
        notebook.add(self.add_tab, text="Soru Ekle")
        notebook.add(self.list_tab, text="Soru Listesi")

        self._build_study_tab()
        self._build_add_tab()
        self._build_list_tab()

    def _build_study_tab(self) -> None:
        self.study_tab.columnconfigure(0, weight=4)
        self.study_tab.columnconfigure(1, weight=1, minsize=280)
        self.study_tab.rowconfigure(0, weight=1)

        left = tk.Frame(self.study_tab, bg=COLORS["card"], highlightthickness=1, highlightbackground=COLORS["line"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        question_head = tk.Frame(left, bg=COLORS["card"])
        question_head.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        question_head.columnconfigure(1, weight=1)

        ttk.Label(question_head, text="Soru", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.question_counter_label = ttk.Label(question_head, text="", style="Metric.TLabel")
        self.question_counter_label.grid(row=0, column=1, sticky="e")
        self.question_subject_label = ttk.Label(question_head, text="", style="CardBody.TLabel")
        self.question_subject_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        body = tk.Frame(left, bg=COLORS["card"])
        body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 18))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        self.question_text = tk.Text(
            body,
            wrap="word",
            font=("Bahnschrift", 16),
            state="disabled",
            relief="flat",
            bd=0,
            padx=0,
            pady=0,
            background=COLORS["card"],
            foreground=COLORS["text"],
            insertbackground=COLORS["text"],
            highlightthickness=0,
        )
        self.question_text.grid(row=0, column=0, sticky="nsew")

        options_shell = tk.Frame(left, bg=COLORS["card"])
        options_shell.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))
        options_shell.columnconfigure(0, weight=1)

        self.option_buttons: list[tk.Radiobutton] = []
        for index, label in enumerate(OPTION_LABELS):
            button = tk.Radiobutton(
                options_shell,
                text=f"{label}) ",
                value=index,
                variable=self.current_answer,
                indicatoron=False,
                anchor="w",
                justify="left",
                padx=16,
                pady=13,
                bd=0,
                relief="flat",
                highlightthickness=1,
                highlightbackground=COLORS["line"],
                activebackground=COLORS["accent_soft"],
                activeforeground=COLORS["accent_dark"],
                bg=COLORS["card"],
                fg=COLORS["text"],
                selectcolor=COLORS["accent_soft"],
                font=("Segoe UI", 11),
            )
            button.grid(row=index, column=0, sticky="ew", pady=6)
            self.option_buttons.append(button)

        right = tk.Frame(self.study_tab, bg=COLORS["surface"], highlightthickness=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        control_card = tk.Frame(right, bg=COLORS["surface"], highlightthickness=0)
        control_card.grid(row=0, column=0, sticky="ew")
        control_card.columnconfigure(0, weight=1)

        ttk.Label(control_card, text="Calisma Kontrolu", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", padx=4, pady=(0, 4))
        ttk.Label(control_card, text="Sorulari filtrele ve akisi yonet.", style="CardBody.TLabel").grid(
            row=1, column=0, sticky="w", padx=4, pady=(0, 12)
        )

        filter_box = ttk.Frame(control_card, style="Surface.TFrame")
        filter_box.grid(row=2, column=0, sticky="ew")
        filter_box.columnconfigure(0, weight=1)

        ttk.Label(filter_box, text="Ders", style="Field.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.subject_combo = ttk.Combobox(
            filter_box,
            textvariable=self.study_subject,
            state="readonly",
            style="App.TCombobox",
        )
        self.subject_combo.grid(row=1, column=0, sticky="ew")
        self.subject_combo.bind("<<ComboboxSelected>>", lambda _event: self.prepare_study_queue())

        self.study_info = ttk.Label(control_card, text="", style="Status.TLabel")
        self.study_info.grid(row=3, column=0, sticky="w", padx=4, pady=(12, 8))

        button_box = ttk.Frame(control_card, style="Surface.TFrame")
        button_box.grid(row=4, column=0, sticky="ew")
        button_box.columnconfigure(0, weight=1)

        ttk.Button(button_box, text="Siradaki Soru", command=self.show_next_question, style="Primary.TButton").grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(button_box, text="Rastgele Soru", command=self.pick_random_question, style="Secondary.TButton").grid(row=1, column=0, sticky="ew")

        self.result_label = ttk.Label(control_card, text="", style="Status.TLabel")
        self.result_label.grid(row=5, column=0, sticky="w", padx=4, pady=(12, 6))

        ttk.Button(control_card, text="Cevabi Kontrol Et", command=self.check_answer, style="Primary.TButton").grid(
            row=6, column=0, sticky="ew", pady=(0, 8)
        )

        note_card = tk.Frame(right, bg=COLORS["surface"], highlightthickness=0)
        note_card.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
        note_card.columnconfigure(0, weight=1)
        note_card.rowconfigure(1, weight=1)

        ttk.Label(note_card, text="Aciklama", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", padx=4, pady=(0, 6))
        self.explanation_label = ttk.Label(
            note_card,
            text="Cevabi kontrol ettikten sonra aciklama burada gorunecek.",
            background=COLORS["surface"],
            foreground=COLORS["muted"],
            wraplength=280,
            justify="left",
            font=("Segoe UI", 10),
        )
        self.explanation_label.grid(row=1, column=0, sticky="nw", padx=4, pady=(0, 8))

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

        ttk.Label(form, text="Ders", style="Field.TLabel").grid(row=0, column=0, sticky="w", pady=8, padx=(0, 16))
        self.subject_entry = ttk.Entry(form, style="App.TEntry")
        self.subject_entry.grid(row=0, column=1, sticky="ew", pady=8)

        ttk.Label(form, text="Soru", style="Field.TLabel").grid(row=1, column=0, sticky="nw", pady=8, padx=(0, 16))
        self.question_entry = self._build_textbox(form, height=8)
        self.question_entry.grid(row=1, column=1, sticky="ew", pady=8)

        self.option_entries = []
        for index, label in enumerate(OPTION_LABELS, start=2):
            ttk.Label(form, text=f"Secenek {label}", style="Field.TLabel").grid(row=index, column=0, sticky="w", pady=8, padx=(0, 16))
            entry = ttk.Entry(form, style="App.TEntry")
            entry.grid(row=index, column=1, sticky="ew", pady=8)
            self.option_entries.append(entry)

        ttk.Label(form, text="Dogru Cevap", style="Field.TLabel").grid(row=6, column=0, sticky="w", pady=8, padx=(0, 16))
        answer_combo = ttk.Combobox(
            form,
            textvariable=self.add_correct_answer,
            values=list(OPTION_LABELS),
            state="readonly",
            width=12,
            style="App.TCombobox",
        )
        answer_combo.grid(row=6, column=1, sticky="w", pady=8)

        ttk.Label(form, text="Aciklama", style="Field.TLabel").grid(row=7, column=0, sticky="nw", pady=8, padx=(0, 16))
        self.explanation_entry = self._build_textbox(form, height=5)
        self.explanation_entry.grid(row=7, column=1, sticky="ew", pady=8)

        buttons = ttk.Frame(form, style="Card.TFrame")
        buttons.grid(row=8, column=1, sticky="w", pady=(16, 0))
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

        columns = ("subject", "question", "correct")
        self.question_tree = ttk.Treeview(table_shell, columns=columns, show="headings", style="App.Treeview")
        self.question_tree.grid(row=0, column=0, sticky="nsew", padx=(0, 0), pady=8)
        self.question_tree.heading("subject", text="Ders")
        self.question_tree.heading("question", text="Soru")
        self.question_tree.heading("correct", text="Dogru")
        self.question_tree.column("subject", width=180, anchor="w")
        self.question_tree.column("question", width=660, anchor="w")
        self.question_tree.column("correct", width=100, anchor="center")
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
                    question.subject,
                    question_preview,
                    OPTION_LABELS[question.correct_option] if 0 <= question.correct_option < len(OPTION_LABELS) else "?",
                ),
                tags=("even" if index % 2 == 0 else "odd",),
            )
            self.tree_question_map[item_id] = question

        total = len(self.questions)
        self.list_info_label.config(text=f"Toplam {total} soru")

    def refresh_subject_filter(self) -> None:
        subjects = sorted({question.subject for question in self.questions if question.subject})
        values = ["Tum Dersler", *subjects]
        self.subject_combo["values"] = values
        if self.study_subject.get() not in values:
            self.study_subject.set("Tum Dersler")

    def prepare_study_queue(self) -> None:
        subject = self.study_subject.get()
        if subject == "Tum Dersler":
            self.filtered_questions = list(self.questions)
        else:
            self.filtered_questions = [question for question in self.questions if question.subject == subject]

        random.shuffle(self.filtered_questions)
        self._update_study_labels()
        self.show_next_question()

    def _update_study_labels(self) -> None:
        total = len(self.questions)
        filtered = len(self.filtered_questions)
        if self.current_question is None:
            current_text = "Hazir"
        else:
            current_text = "Soru acik"

        self.study_info.config(text=f"Filtrede {filtered} soru var")
        self.question_counter_label.config(text=f"Havuz {total} | Durum: {current_text}")

    def show_next_question(self) -> None:
        if not self.filtered_questions:
            self.current_question = None
            self._update_study_labels()
            self._render_question(None)
            return

        self.current_question = self.filtered_questions.pop(0)
        self._update_study_labels()
        self._render_question(self.current_question)

    def pick_random_question(self) -> None:
        if not self.questions:
            self.current_question = None
            self._update_study_labels()
            self._render_question(None)
            return

        subject = self.study_subject.get()
        pool = self.questions if subject == "Tum Dersler" else [q for q in self.questions if q.subject == subject]
        if not pool:
            self.current_question = None
            self._update_study_labels()
            self._render_question(None)
            return

        self.current_question = random.choice(pool)
        self._update_study_labels()
        self._render_question(self.current_question)

    def _render_question(self, question: Question | None) -> None:
        self.current_answer.set(-1)
        self.result_label.config(text="", foreground=COLORS["muted"])
        self.explanation_label.config(text="Cevabi kontrol ettikten sonra aciklama burada gorunecek.")

        self.question_text.config(state="normal")
        self.question_text.delete("1.0", tk.END)

        if question is None:
            self.question_subject_label.config(text="Bu filtrede soru yok")
            self.question_text.insert("1.0", "Soldaki ana alan bos kalmasin diye mesaj gosteriliyor. Ders filtresini degistirebilir veya yeni soru ekleyebilirsiniz.")
            self.question_text.config(state="disabled")
            for index, button in enumerate(self.option_buttons):
                button.config(text=f"{OPTION_LABELS[index]}) -", state="disabled", bg=COLORS["neutral_bg"], fg=COLORS["muted"])
            return

        self.question_subject_label.config(text=f"Ders: {question.subject}")
        self.question_text.insert("1.0", question.text)
        self.question_text.config(state="disabled")

        for index, button in enumerate(self.option_buttons):
            option_text = question.options[index] if index < len(question.options) else "-"
            button.config(
                text=f"{OPTION_LABELS[index]}) {option_text}",
                state="normal",
                bg=COLORS["neutral_bg"],
                fg=COLORS["text"],
            )

    def check_answer(self) -> None:
        if self.current_question is None:
            messagebox.showinfo("Bilgi", "Kontrol edilecek soru yok.")
            return

        selected = self.current_answer.get()
        if selected < 0:
            messagebox.showwarning("Uyari", "Lutfen bir cevap secin.")
            return

        correct_index = self.current_question.correct_option
        correct_label = OPTION_LABELS[correct_index]

        for index, button in enumerate(self.option_buttons):
            if index == correct_index:
                button.config(bg=COLORS["success_bg"], fg=COLORS["success_fg"])
            elif index == selected:
                button.config(bg=COLORS["danger_bg"], fg=COLORS["danger_fg"])
            else:
                button.config(bg=COLORS["neutral_bg"], fg=COLORS["text"])

        if selected == correct_index:
            self.result_label.config(text=f"Dogru cevap: {correct_label}", foreground=COLORS["success_fg"])
        else:
            self.result_label.config(text=f"Yanlis. Dogru cevap: {correct_label}", foreground=COLORS["danger_fg"])

        if self.current_question.explanation:
            self.explanation_label.config(text=self.current_question.explanation, foreground=COLORS["text"])
        else:
            self.explanation_label.config(text="Bu soru icin aciklama eklenmemis.", foreground=COLORS["muted"])

    def save_question(self) -> None:
        subject = self.subject_entry.get().strip()
        question_text = self.question_entry.get("1.0", tk.END).strip()
        options = [entry.get().strip() for entry in self.option_entries]
        explanation = self.explanation_entry.get("1.0", tk.END).strip()
        correct_option = OPTION_LABELS.index(self.add_correct_answer.get())

        if not subject:
            messagebox.showwarning("Eksik Bilgi", "Ders alani bos olamaz.")
            return
        if not question_text:
            messagebox.showwarning("Eksik Bilgi", "Soru metni bos olamaz.")
            return
        if any(not option for option in options):
            messagebox.showwarning("Eksik Bilgi", "Tum secenekleri doldurun.")
            return

        question = Question(
            subject=subject,
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
        self.refresh_subject_filter()
        self.prepare_study_queue()

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
        self.refresh_subject_filter()
        self.prepare_study_queue()

    def clear_form(self, clear_status: bool = True) -> None:
        self.subject_entry.delete(0, tk.END)
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
