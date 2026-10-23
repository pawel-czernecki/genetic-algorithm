from datetime import datetime
from pathlib import Path
import statistics
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from engine.algorithm import GeneticAlgorithm
from engine.crossover import Crossover
from engine.functions import FunctionRegistry
from engine.mutation import Mutation
from engine.selection import Selection


class GeneticAlgorithmGUI:
    """Główna klasa interfejsu graficznego (Tkinter/ttk + Matplotlib) dla klasycznego algorytmu genetycznego."""

    SELECTION_MAP = {
        "Turniejowa (Tournament)": Selection.tournament,
        "Najlepszych (Best)": Selection.best,
        "Najgorszych (Worst)": Selection.worst,
        "Koło ruletki (Roulette)": Selection.roulette,
    }

    CROSSOVER_MAP = {
        "Jednopunktowe (One-point)": Crossover.onepoint_crossover,
        "Dwupunktowe (Two-point)": Crossover.twopoint_crossover,
        "Jednorodne (Uniform)": Crossover.uniform_crossover,
        "Ziarniste (Granular)": Crossover.granular,
    }

    MUTATION_MAP = {
        "Jednopunktowa (One-point)": Mutation.onepoint_mutation,
        "Dwupunktowa (Two-point)": Mutation.twopoint_mutation,
        "Brzegowa (Edge)": Mutation.edge_mutation,
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Projekt 1 – Klasyczny Algorytm Genetyczny (Obliczenia Ewolucyjne)")
        self.root.geometry("1360x860")
        self.root.minsize(1120, 740)

        self.last_ga: GeneticAlgorithm | None = None
        self.last_metadata: dict = {}
        self.is_running = False
        self.results_dir = Path(__file__).resolve().parent.parent / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self._init_variables()
        self._build_layout()
        self._on_function_change()
        self._on_selection_change()

    def _init_variables(self):
        functions = FunctionRegistry.get_all()
        self.var_function = tk.StringVar(value=functions[0].name)
        self.var_opt_type = tk.StringVar(value="min")
        self.var_num_vars = tk.IntVar(value=10)
        self.var_bound_min = tk.DoubleVar(value=functions[0].default_bounds[0])
        self.var_bound_max = tk.DoubleVar(value=functions[0].default_bounds[1])

        self.var_precision_mode = tk.StringVar(value="bits")
        self.var_bit_precision = tk.IntVar(value=16)
        self.var_decimal_precision = tk.IntVar(value=4)

        self.var_pop_size = tk.IntVar(value=80)
        self.var_epochs = tk.IntVar(value=150)
        self.var_num_runs = tk.IntVar(value=1)

        self.var_selection = tk.StringVar(value="Turniejowa (Tournament)")
        self.var_selection_param = tk.DoubleVar(value=3.0)

        self.var_crossover = tk.StringVar(value="Dwupunktowe (Two-point)")
        self.var_cross_prob = tk.DoubleVar(value=0.8)

        self.var_mutation = tk.StringVar(value="Jednopunktowa (One-point)")
        self.var_mut_prob = tk.DoubleVar(value=0.3)

        self.var_inv_prob = tk.DoubleVar(value=0.3)

        self.var_elite_mode = tk.StringVar(value="percent")
        self.var_elite_value = tk.DoubleVar(value=10.0)

        self.var_auto_save_csv = tk.BooleanVar(value=False)
        self.var_auto_save_json = tk.BooleanVar(value=False)
        self.var_auto_save_charts = tk.BooleanVar(value=False)
        self.var_status = tk.StringVar(value="Gotowy do uruchomienia.")
        self.var_exec_time = tk.StringVar(value="—")
        self.var_res_epochs = tk.StringVar(value="—")
        self.var_res_fx = tk.StringVar(value="—")
        self.var_res_opt_err = tk.StringVar(value="—")
        self.var_res_stats = tk.StringVar(value="Pojedyncze uruchomienie (ustaw 10 powtórzeń dla statystyk do sprawozdania)")

    def _build_layout(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Przewijany panel lewy z konfiguracją parametrów
        left_wrapper = ttk.Frame(main_pane, width=440)
        main_pane.add(left_wrapper, weight=0)

        left_canvas = tk.Canvas(left_wrapper, width=420, highlightthickness=0, borderwidth=0)
        left_scrollbar = ttk.Scrollbar(left_wrapper, orient=tk.VERTICAL, command=left_canvas.yview)
        left_content = ttk.Frame(left_canvas)

        left_content.bind(
            "<Configure>",
            lambda _e: left_canvas.configure(scrollregion=left_canvas.bbox("all")),
        )
        canvas_window = left_canvas.create_window((0, 0), window=left_content, anchor="nw")
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        def _on_canvas_resize(event):
            left_canvas.itemconfig(canvas_window, width=event.width)

        left_canvas.bind("<Configure>", _on_canvas_resize)

        # Obsługa przewijania kółkiem myszy
        def _on_mousewheel(event):
            if left_canvas.winfo_exists():
                if event.num == 4:
                    left_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    left_canvas.yview_scroll(1, "units")
                elif event.delta:
                    left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        left_canvas.bind("<Enter>", lambda _e: left_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        left_canvas.bind("<Leave>", lambda _e: left_canvas.unbind_all("<MouseWheel>"))

        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        right_container = ttk.Frame(main_pane)
        main_pane.add(right_container, weight=1)

        self._build_config_panel(left_content)
        self._build_results_panel(right_container)

    def _build_config_panel(self, parent):
        # Sekcja 1: Funkcja celu i zmienne
        func_frame = ttk.LabelFrame(parent, text="1. Funkcja celu i przestrzeń poszukiwań", padding=6)
        func_frame.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(func_frame, text="Funkcja testowa:").grid(row=0, column=0, sticky=tk.W, pady=1)
        func_names = [f.name for f in FunctionRegistry.get_all()]
        cb_func = ttk.Combobox(func_frame, textvariable=self.var_function, values=func_names, state="readonly", width=36)
        cb_func.grid(row=0, column=1, columnspan=3, sticky=tk.EW, pady=1)
        cb_func.bind("<<ComboboxSelected>>", lambda _e: self._on_function_change())

        self.lbl_func_desc = ttk.Label(func_frame, text="", wraplength=380, foreground="#333333", font=("TkDefaultFont", 8))
        self.lbl_func_desc.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(1, 3))

        ttk.Label(func_frame, text="Typ optymalizacji:").grid(row=2, column=0, sticky=tk.W, pady=1)
        opt_sub = ttk.Frame(func_frame)
        opt_sub.grid(row=2, column=1, columnspan=3, sticky=tk.W)
        ttk.Radiobutton(opt_sub, text="Minimalizacja (min)", variable=self.var_opt_type, value="min").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(opt_sub, text="Maksymalizacja (max)", variable=self.var_opt_type, value="max").pack(side=tk.LEFT)

        ttk.Label(func_frame, text="Liczba zmiennych (N):").grid(row=3, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(func_frame, from_=1, to=200, textvariable=self.var_num_vars, width=12).grid(
            row=3, column=1, sticky=tk.W, pady=1
        )

        ttk.Label(func_frame, text="Przedział [min, max]:").grid(row=4, column=0, sticky=tk.W, pady=1)
        bounds_sub = ttk.Frame(func_frame)
        bounds_sub.grid(row=4, column=1, columnspan=3, sticky=tk.W)
        ttk.Entry(bounds_sub, textvariable=self.var_bound_min, width=10).pack(side=tk.LEFT)
        ttk.Label(bounds_sub, text=" do ").pack(side=tk.LEFT)
        ttk.Entry(bounds_sub, textvariable=self.var_bound_max, width=10).pack(side=tk.LEFT)

        func_frame.columnconfigure(1, weight=1)

        # Sekcja 2: Chromosom i populacja
        pop_frame = ttk.LabelFrame(parent, text="2. Reprezentacja binarna i populacja", padding=6)
        pop_frame.pack(fill=tk.X, pady=(0, 4))

        ttk.Radiobutton(
            pop_frame,
            text="Liczba bitów na zmienną:",
            variable=self.var_precision_mode,
            value="bits",
        ).grid(row=0, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(pop_frame, from_=2, to=64, textvariable=self.var_bit_precision, width=10).grid(row=0, column=1, sticky=tk.W, pady=1)

        ttk.Radiobutton(
            pop_frame,
            text="Dokładność dziesiętna d (10^-d):",
            variable=self.var_precision_mode,
            value="decimal",
        ).grid(row=1, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(pop_frame, from_=1, to=12, textvariable=self.var_decimal_precision, width=10).grid(row=1, column=1, sticky=tk.W, pady=1)

        ttk.Label(pop_frame, text="Wielkość populacji:").grid(row=2, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(pop_frame, from_=4, to=5000, increment=10, textvariable=self.var_pop_size, width=10).grid(row=2, column=1, sticky=tk.W, pady=1)

        ttk.Label(pop_frame, text="Liczba epok (iteracji):").grid(row=3, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(pop_frame, from_=1, to=10000, increment=50, textvariable=self.var_epochs, width=10).grid(row=3, column=1, sticky=tk.W, pady=1)

        # Sekcja 3: Operatory genetyczne
        op_frame = ttk.LabelFrame(parent, text="3. Selekcja, krzyżowanie, mutacja, inwersja", padding=6)
        op_frame.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(op_frame, text="Metoda selekcji:").grid(row=0, column=0, sticky=tk.W, pady=1)
        cb_sel = ttk.Combobox(
            op_frame,
            textvariable=self.var_selection,
            values=list(self.SELECTION_MAP.keys()),
            state="readonly",
            width=25,
        )
        cb_sel.grid(row=0, column=1, sticky=tk.EW, pady=1)
        cb_sel.bind("<<ComboboxSelected>>", lambda _e: self._on_selection_change())

        self.lbl_sel_param = ttk.Label(op_frame, text="Rozmiar turnieju (k):")
        self.lbl_sel_param.grid(row=1, column=0, sticky=tk.W, pady=1)
        self.ent_sel_param = ttk.Entry(op_frame, textvariable=self.var_selection_param, width=10)
        self.ent_sel_param.grid(row=1, column=1, sticky=tk.W, pady=1)

        ttk.Label(op_frame, text="Metoda krzyżowania:").grid(row=2, column=0, sticky=tk.W, pady=1)
        ttk.Combobox(
            op_frame,
            textvariable=self.var_crossover,
            values=list(self.CROSSOVER_MAP.keys()),
            state="readonly",
            width=25,
        ).grid(row=2, column=1, sticky=tk.EW, pady=1)

        ttk.Label(op_frame, text="Prawdop. krzyżowania (p_c):").grid(row=3, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(op_frame, from_=0.0, to=1.0, increment=0.05, textvariable=self.var_cross_prob, width=10).grid(row=3, column=1, sticky=tk.W, pady=1)

        ttk.Label(op_frame, text="Metoda mutacji:").grid(row=4, column=0, sticky=tk.W, pady=1)
        ttk.Combobox(
            op_frame,
            textvariable=self.var_mutation,
            values=list(self.MUTATION_MAP.keys()),
            state="readonly",
            width=25,
        ).grid(row=4, column=1, sticky=tk.EW, pady=1)

        ttk.Label(op_frame, text="Prawdop. mutacji (p_m):").grid(row=5, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(op_frame, from_=0.0, to=1.0, increment=0.01, textvariable=self.var_mut_prob, width=10).grid(row=5, column=1, sticky=tk.W, pady=1)

        ttk.Label(op_frame, text="Prawdop. inwersji (p_i):").grid(row=6, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(op_frame, from_=0.0, to=1.0, increment=0.01, textvariable=self.var_inv_prob, width=10).grid(row=6, column=1, sticky=tk.W, pady=1)

        op_frame.columnconfigure(1, weight=1)

        # Sekcja 4: Strategia elitarna i eksperyment wielokrotny
        elite_frame = ttk.LabelFrame(parent, text="4. Strategia elitarna i uruchomienia", padding=6)
        elite_frame.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(elite_frame, text="Tryb elitaryzmu:").grid(row=0, column=0, sticky=tk.W, pady=1)
        elite_sub = ttk.Frame(elite_frame)
        elite_sub.grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(elite_sub, text="% populacji", variable=self.var_elite_mode, value="percent").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Radiobutton(elite_sub, text="Liczba osobników", variable=self.var_elite_mode, value="count").pack(side=tk.LEFT)

        ttk.Label(elite_frame, text="Wartość elity (% lub szt.):").grid(row=1, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(elite_frame, from_=0, to=100, increment=1, textvariable=self.var_elite_value, width=10).grid(row=1, column=1, sticky=tk.W, pady=1)

        ttk.Label(elite_frame, text="Liczba powtórzeń (uruchomień):").grid(row=2, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(elite_frame, from_=1, to=100, textvariable=self.var_num_runs, width=10).grid(row=2, column=1, sticky=tk.W, pady=1)

        ttk.Checkbutton(
            elite_frame,
            text="Automatycznie zapisuj iteracje do CSV (results/)",
            variable=self.var_auto_save_csv,
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(2, 1))

        ttk.Checkbutton(
            elite_frame,
            text="Automatycznie zapisuj iteracje do JSON (results/)",
            variable=self.var_auto_save_json,
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(1, 1))

        ttk.Checkbutton(
            elite_frame,
            text="Automatycznie zapisuj wykresy PNG (results/)",
            variable=self.var_auto_save_charts,
        ).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(1, 2))

        # Przyciski sterujące
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=3)

        self.btn_run = ttk.Button(btn_frame, text="▶ Uruchom algorytm", command=self.start_algorithm)
        self.btn_run.pack(fill=tk.X, pady=(1, 3), ipady=3)

        export_sub = ttk.Frame(btn_frame)
        export_sub.pack(fill=tk.X, pady=1)
        ttk.Button(export_sub, text="Eksportuj CSV...", command=self.export_csv_dialog).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(export_sub, text="Eksportuj JSON...", command=self.export_json_dialog).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        self.progress = ttk.Progressbar(parent, orient=tk.HORIZONTAL, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(3, 1))
        ttk.Label(parent, textvariable=self.var_status, foreground="#005580").pack(anchor=tk.W)

    def _build_results_panel(self, parent):
        summary_frame = ttk.LabelFrame(parent, text="Podsumowanie obliczeń i wyniki", padding=8)
        summary_frame.pack(fill=tk.X, pady=(0, 6))

        # Górny rząd osobnych okienek z kluczowymi metrykami: Czas, Epoki, f(x), Optimum i błąd
        cards_frame = ttk.Frame(summary_frame)
        cards_frame.pack(fill=tk.X, pady=(0, 6))
        for col_idx in range(4):
            cards_frame.columnconfigure(col_idx, weight=1)

        card_time = ttk.LabelFrame(cards_frame, text="Czas wykonania", padding=6)
        card_time.grid(row=0, column=0, sticky=tk.EW, padx=(0, 4))
        ent_time = ttk.Entry(
            card_time,
            textvariable=self.var_exec_time,
            state="readonly",
            font=("Consolas", 11, "bold"),
            justify=tk.CENTER,
        )
        ent_time.pack(fill=tk.X)

        card_epochs = ttk.LabelFrame(cards_frame, text="Epoki i chromosom", padding=6)
        card_epochs.grid(row=0, column=1, sticky=tk.EW, padx=4)
        ent_epochs = ttk.Entry(
            card_epochs,
            textvariable=self.var_res_epochs,
            state="readonly",
            font=("Consolas", 10, "bold"),
            justify=tk.CENTER,
        )
        ent_epochs.pack(fill=tk.X)

        card_fx = ttk.LabelFrame(cards_frame, text="Najlepsza wartość f(x)", padding=6)
        card_fx.grid(row=0, column=2, sticky=tk.EW, padx=4)
        ent_fx = ttk.Entry(
            card_fx,
            textvariable=self.var_res_fx,
            state="readonly",
            font=("Consolas", 11, "bold"),
            justify=tk.CENTER,
        )
        ent_fx.pack(fill=tk.X)

        card_err = ttk.LabelFrame(cards_frame, text="Optimum f* oraz błąd |f(x) - f*|", padding=6)
        card_err.grid(row=0, column=3, sticky=tk.EW, padx=(4, 0))
        ent_err = ttk.Entry(
            card_err,
            textvariable=self.var_res_opt_err,
            state="readonly",
            font=("Consolas", 10),
            justify=tk.CENTER,
        )
        ent_err.pack(fill=tk.X)

        # Osobne okienko na wektor znalezionych argumentów x = (x1, x2, ..., xN)
        x_frame = ttk.LabelFrame(summary_frame, text="Znalezione argumenty x = (x₁, x₂, ..., xₙ)", padding=6)
        x_frame.pack(fill=tk.X, pady=(0, 4))

        x_scroll = ttk.Scrollbar(x_frame, orient=tk.VERTICAL)
        self.txt_x_values = tk.Text(
            x_frame,
            height=2,
            wrap=tk.WORD,
            font=("Consolas", 10),
            yscrollcommand=x_scroll.set,
            bg="#fcfcfc",
        )
        x_scroll.configure(command=self.txt_x_values.yview)
        self.txt_x_values.pack(side=tk.LEFT, fill=tk.X, expand=True)
        x_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_x_values.insert(tk.END, "Uruchom algorytm, aby zobaczyć wektor najlepszych zmiennych x.")
        self.txt_x_values.configure(state=tk.DISABLED)

        # Pasek statystyk wielokrotnych uruchomień i zapisanych plików
        stats_box = ttk.Frame(summary_frame)
        stats_box.pack(fill=tk.X)
        ttk.Label(stats_box, textvariable=self.var_res_stats, font=("Consolas", 9), foreground="#333333").pack(
            side=tk.LEFT, anchor=tk.W
        )

        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_plot_best = ttk.Frame(self.notebook)
        self.tab_plot_stats = ttk.Frame(self.notebook)
        self.tab_table = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_plot_best, text="Wykres 9a: Wartość funkcji celu")
        self.notebook.add(self.tab_plot_stats, text="Wykres 9b: Średnia i odchylenie std")
        self.notebook.add(self.tab_table, text="Tabela kolejnych iteracji (pkt 10)")

        self._build_plot_best_area(self.tab_plot_best)
        self._build_plot_stats_area(self.tab_plot_stats)
        self._build_table_area(self.tab_table)

    def _build_plot_best_area(self, parent):
        top_bar = ttk.Frame(parent)
        top_bar.pack(fill=tk.X, padx=6, pady=4)
        ttk.Label(
            top_bar,
            text="Wykres 9a: Zależność wartości funkcji celu od kolejnej iteracji",
            font=("TkDefaultFont", 9, "bold"),
        ).pack(side=tk.LEFT)

        self.figure_best = Figure(figsize=(8.5, 5.2), dpi=100)
        self.ax_best = self.figure_best.add_subplot(1, 1, 1)
        self.figure_best.tight_layout(pad=3.0)

        self.canvas_best = FigureCanvasTkAgg(self.figure_best, master=parent)
        self.canvas_best.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas_best, toolbar_frame)
        toolbar.update()

    def _build_plot_stats_area(self, parent):
        top_bar = ttk.Frame(parent)
        top_bar.pack(fill=tk.X, padx=6, pady=4)
        ttk.Label(
            top_bar,
            text="Wykres 9b: Średnia wartość funkcji celu oraz odchylenie standardowe od kolejnej iteracji",
            font=("TkDefaultFont", 9, "bold"),
        ).pack(side=tk.LEFT)

        self.figure_stats = Figure(figsize=(8.5, 5.2), dpi=100)
        self.ax_stats = self.figure_stats.add_subplot(1, 1, 1)
        self.figure_stats.tight_layout(pad=3.0)

        self.canvas_stats = FigureCanvasTkAgg(self.figure_stats, master=parent)
        self.canvas_stats.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas_stats, toolbar_frame)
        toolbar.update()

    def _build_table_area(self, parent):
        table_top = ttk.Frame(parent)
        table_top.pack(fill=tk.X, padx=6, pady=4)
        ttk.Label(table_top, text="Tabela wyników z kolejnych epok algorytmu:", font=("TkDefaultFont", 9, "bold")).pack(side=tk.LEFT)
        ttk.Button(table_top, text="Eksportuj tabelę do JSON...", command=self.export_json_dialog).pack(side=tk.RIGHT, padx=(2, 0))
        ttk.Button(table_top, text="Eksportuj tabelę do CSV...", command=self.export_csv_dialog).pack(side=tk.RIGHT, padx=(0, 2))

        cols = ("epoch", "best_fitness", "global_best", "mean_fitness", "std_fitness", "worst_fitness", "elapsed_time")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=18)
        headers = {
            "epoch": "Epoka (Iteracja)",
            "best_fitness": "Najlepszy w epoce",
            "global_best": "Najlepszy globalnie",
            "mean_fitness": "Średnia wartość funkcji",
            "std_fitness": "Odchylenie std",
            "worst_fitness": "Najgorszy w epoce",
            "elapsed_time": "Czas [s]",
        }
        for col, title in headers.items():
            self.tree.heading(col, text=title)
            self.tree.column(col, width=120, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_function_change(self):
        spec = FunctionRegistry.get_by_name(self.var_function.get())
        self.var_bound_min.set(spec.default_bounds[0])
        self.var_bound_max.set(spec.default_bounds[1])
        self.lbl_func_desc.configure(text=spec.description)

    def _on_selection_change(self):
        sel_name = self.var_selection.get()
        if "Turniejowa" in sel_name:
            self.lbl_sel_param.configure(text="Rozmiar turnieju (k):")
            self.ent_sel_param.configure(state=tk.NORMAL)
            if self.var_selection_param.get() <= 1.0:
                self.var_selection_param.set(3.0)
        elif "Ruletki" in sel_name or "Roulette" in sel_name:
            self.lbl_sel_param.configure(text="Parametr selekcji (brak):")
            self.ent_sel_param.configure(state=tk.DISABLED)
        else:
            self.lbl_sel_param.configure(text="Pula osobników (ułamek 0-1 lub liczba):")
            self.ent_sel_param.configure(state=tk.NORMAL)
            if self.var_selection_param.get() >= 2.0:
                self.var_selection_param.set(0.5)

    def _set_x_values_text(self, text: str):
        self.txt_x_values.configure(state=tk.NORMAL)
        self.txt_x_values.delete("1.0", tk.END)
        self.txt_x_values.insert(tk.END, text)
        self.txt_x_values.configure(state=tk.DISABLED)

    def start_algorithm(self):
        if self.is_running:
            return
        try:
            num_vars = int(self.var_num_vars.get())
            pop_size = int(self.var_pop_size.get())
            epochs = int(self.var_epochs.get())
            num_runs = max(1, int(self.var_num_runs.get()))
            b_min = float(self.var_bound_min.get())
            b_max = float(self.var_bound_max.get())
            if b_min >= b_max:
                raise ValueError("Początek przedziału (min) musi być mniejszy niż koniec (max).")
            cross_prob = float(self.var_cross_prob.get())
            mut_prob = float(self.var_mut_prob.get())
            inv_prob = float(self.var_inv_prob.get())
            sel_param = float(self.var_selection_param.get())
            elite_val = float(self.var_elite_value.get())
        except Exception as exc:
            messagebox.showerror("Błąd konfiguracji", f"Niepoprawne parametry wejściowe:\n{exc}")
            return

        self.is_running = True
        self.btn_run.configure(state=tk.DISABLED)
        self.progress["value"] = 0
        self.progress["maximum"] = epochs * num_runs
        self.var_status.set("Trwają obliczenia ewolucyjne...")

        thread = threading.Thread(
            target=self._run_worker,
            args=(num_vars, pop_size, epochs, num_runs, (b_min, b_max), cross_prob, mut_prob, inv_prob, sel_param, elite_val),
            daemon=True,
        )
        thread.start()

    def _run_worker(self, num_vars, pop_size, epochs, num_runs, bounds, cross_prob, mut_prob, inv_prob, sel_param, elite_val):
        try:
            spec = FunctionRegistry.get_by_name(self.var_function.get())
            fitness_func = spec.create_evaluator(num_vars)
            opt_type = self.var_opt_type.get()

            precision_mode = self.var_precision_mode.get()
            bit_prec = int(self.var_bit_precision.get()) if precision_mode == "bits" else 16
            dec_prec = int(self.var_decimal_precision.get()) if precision_mode == "decimal" else None

            elite_mode = self.var_elite_mode.get()
            elite_percent = (elite_val / 100.0) if elite_mode == "percent" else None
            elite_count = int(elite_val) if elite_mode == "count" else None

            sel_method = self.SELECTION_MAP[self.var_selection.get()]
            cross_method = self.CROSSOVER_MAP[self.var_crossover.get()]
            mut_method = self.MUTATION_MAP[self.var_mutation.get()]

            runs_results = []
            best_ga = None
            best_run_score = None

            for run_idx in range(num_runs):
                ga = GeneticAlgorithm(
                    pop_size=pop_size,
                    epochs=epochs,
                    num_variables=num_vars,
                    bit_precision=bit_prec,
                    bounds=bounds,
                    fitness_func=fitness_func,
                    opt_type=opt_type,
                    elite_percent=elite_percent if elite_percent is not None else 0.0,
                    elite_count=elite_count,
                    decimal_precision=dec_prec,
                )

                def _progress_cb(ep, total_ep, _stats, r_idx=run_idx):
                    completed = r_idx * total_ep + ep
                    if ep % max(1, total_ep // 25) == 0 or ep == total_ep:
                        self.root.after(0, self._update_progress, completed, r_idx + 1, num_runs, ep, total_ep)

                ga.run(
                    selection_method=sel_method,
                    crossover_method=cross_method,
                    mutation_method=mut_method,
                    cross_prob=cross_prob,
                    mut_prob=mut_prob,
                    inv_prob=inv_prob,
                    selection_param=sel_param,
                    progress_callback=_progress_cb,
                    verbose=False,
                )

                best_ind = ga.best_individual or Selection.best(ga.population, 1, opt_type)[0]
                runs_results.append((best_ind.fitness, ga.execution_time, best_ind.decode(), ga))

                is_better = (
                    best_run_score is None
                    or (opt_type == "min" and best_ind.fitness < best_run_score)
                    or (opt_type == "max" and best_ind.fitness > best_run_score)
                )
                if is_better:
                    best_run_score = best_ind.fitness
                    best_ga = ga

            self.last_ga = best_ga
            opt_real_val, opt_real_pos = spec.get_optimum_info(num_vars)

            scores = [r[0] for r in runs_results]
            times = [r[1] for r in runs_results]
            total_time = sum(times)
            mean_time = statistics.fmean(times)
            best_score = min(scores) if opt_type == "min" else max(scores)
            worst_score = max(scores) if opt_type == "min" else min(scores)
            mean_score = statistics.fmean(scores)
            std_score = statistics.pstdev(scores) if len(scores) > 1 else 0.0
            error_val = abs(best_score - opt_real_val) if isinstance(opt_real_val, (int, float)) else None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.last_metadata = {
                "timestamp": timestamp,
                "function_name": spec.name,
                "num_variables": num_vars,
                "opt_type": opt_type,
                "selection": self.var_selection.get(),
                "selection_param": sel_param,
                "crossover": self.var_crossover.get(),
                "cross_prob": cross_prob,
                "mutation": self.var_mutation.get(),
                "mut_prob": mut_prob,
                "inv_prob": inv_prob,
                "num_runs": num_runs,
                "runs_summary": {
                    "best_score": best_score,
                    "worst_score": worst_score,
                    "mean_score": mean_score,
                    "std_score": std_score,
                    "mean_time_sec": mean_time,
                    "total_time_sec": total_time,
                    "theoretical_optimum": opt_real_val,
                    "abs_error": error_val,
                },
            }

            saved_files = []
            if best_ga is not None:
                if self.var_auto_save_csv.get():
                    csv_path = self.results_dir / f"wyniki_{spec.key}_N{num_vars}_{timestamp}.csv"
                    best_ga.save_history_csv(csv_path, metadata=self.last_metadata)
                    saved_files.append(csv_path.name)
                if self.var_auto_save_json.get():
                    json_path = self.results_dir / f"wyniki_{spec.key}_N{num_vars}_{timestamp}.json"
                    best_ga.save_history_json(json_path, metadata=self.last_metadata)
                    saved_files.append(json_path.name)

            self.root.after(
                0,
                self._on_run_complete,
                spec,
                best_ga,
                runs_results,
                opt_real_val,
                opt_real_pos,
                error_val,
                saved_files,
                timestamp,
            )
        except Exception as exc:
            self.root.after(0, self._on_run_error, str(exc))

    def _update_progress(self, completed, run_no, num_runs, ep, total_ep):
        self.progress["value"] = completed
        self.var_status.set(f"Uruchomienie {run_no}/{num_runs} | Epoka {ep}/{total_ep}...")

    def _on_run_error(self, err_msg):
        self.is_running = False
        self.btn_run.configure(state=tk.NORMAL)
        self.var_status.set("Błąd podczas wykonywania algorytmu.")
        messagebox.showerror("Błąd wykonania", err_msg)

    def _on_run_complete(self, spec, best_ga, runs_results, opt_real_val, opt_real_pos, error_val, saved_files, timestamp=None):
        self.is_running = False
        self.btn_run.configure(state=tk.NORMAL)

        scores = [r[0] for r in runs_results]
        times = [r[1] for r in runs_results]
        total_time = sum(times)
        mean_time = statistics.fmean(times)
        num_runs = len(runs_results)

        if num_runs == 1:
            self.var_exec_time.set(f"{total_time:.4f} s")
        else:
            self.var_exec_time.set(f"{mean_time:.4f} s (śr. z {num_runs}x)")

        total_bits = best_ga.num_variables * best_ga.bit_precision
        self.var_res_epochs.set(f"{best_ga.epochs} epok | N={best_ga.num_variables} ({total_bits} b)")

        best_ind = best_ga.best_individual or Selection.best(best_ga.population, 1, best_ga.opt_type)[0]
        self.var_res_fx.set(f"{best_ind.fitness:.6f}")

        err_str = f"{error_val:.6f}" if error_val is not None else "n/d"
        opt_str = f"{opt_real_val:.4f}" if isinstance(opt_real_val, (int, float)) else str(opt_real_val)
        self.var_res_opt_err.set(f"f*={opt_str} | Δ={err_str}")

        decoded_vars = best_ind.decode()
        formatted_x = ",  ".join(f"x{i+1} = {v:.6f}" for i, v in enumerate(decoded_vars))
        self._set_x_values_text(formatted_x)

        self._populate_table(best_ga.history)
        self._update_plots(best_ga.history, spec.name, best_ga.num_variables, runs_results=runs_results, best_ga=best_ga)

        # Automatyczny zapis wykresów (jeśli zaznaczono checkbox)
        if self.var_auto_save_charts.get() and best_ga is not None and best_ga.history:
            ts = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
            chart_9a = self.results_dir / f"wykres_9a_{spec.key}_N{best_ga.num_variables}_{ts}.png"
            chart_9b = self.results_dir / f"wykres_9b_{spec.key}_N{best_ga.num_variables}_{ts}.png"
            try:
                self.figure_best.savefig(chart_9a, dpi=180, bbox_inches="tight")
                self.figure_stats.savefig(chart_9b, dpi=180, bbox_inches="tight")
                saved_files.extend([chart_9a.name, chart_9b.name])
            except Exception as exc:
                print(f"Błąd zapisu wykresów: {exc}")

        if num_runs > 1:
            mean_s = statistics.fmean(scores)
            std_s = statistics.pstdev(scores)
            best_s = min(scores) if best_ga.opt_type == "min" else max(scores)
            worst_s = max(scores) if best_ga.opt_type == "min" else min(scores)
            stats_line = (
                f"Seria {num_runs} uruchomień -> Średnia f(x): {mean_s:.6f} | Odch. std: {std_s:.6f} | "
                f"Najlepszy: {best_s:.6f} | Najgorszy: {worst_s:.6f} | Czas łączny: {total_time:.4f} s"
            )
            if saved_files:
                stats_line += f"  |  Zapisano: {', '.join(saved_files)}"
        else:
            stats_line = f"Funkcja: {spec.name}"
            if saved_files:
                stats_line += f"  |  Zapisano: {', '.join(saved_files)}"
        self.var_res_stats.set(stats_line)

        self.var_status.set("Obliczenia zakończone pomyślnie.")

    def _populate_table(self, history):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in history:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    row["epoch"],
                    f"{row['best_fitness']:.6f}",
                    f"{row['global_best_fitness']:.6f}",
                    f"{row['mean_fitness']:.6f}",
                    f"{row['std_fitness']:.6f}",
                    f"{row['worst_fitness']:.6f}",
                    f"{row['elapsed_time_sec']:.4f}",
                ),
            )

    def _update_plots(self, history, func_name, num_vars, runs_results=None, best_ga=None):
        if not history:
            return
        epochs = [h["epoch"] for h in history]
        best_vals = [h["best_fitness"] for h in history]
        global_best_vals = [h["global_best_fitness"] for h in history]
        mean_vals = [h["mean_fitness"] for h in history]
        std_vals = [h["std_fitness"] for h in history]

        # Wykres 9a: Wartość funkcji od kolejnej iteracji (Pkt 9a wytycznych)
        self.ax_best.clear()

        has_multiple_runs = runs_results is not None and len(runs_results) > 1

        if has_multiple_runs:
            # Wyświetlamy pozostałe próby cienką przerywaną linią
            other_plotted = False
            for r_entry in runs_results:
                run_ga = r_entry[3] if len(r_entry) > 3 else None
                if run_ga and run_ga.history and run_ga is not best_ga:
                    r_epochs = [h["epoch"] for h in run_ga.history]
                    r_global = [h["global_best_fitness"] for h in run_ga.history]
                    label = "Pozostałe próby" if not other_plotted else None
                    self.ax_best.plot(
                        r_epochs,
                        r_global,
                        linestyle="--",
                        color="#7f8c8d",
                        linewidth=1.0,
                        alpha=0.55,
                        label=label,
                        zorder=2,
                    )
                    other_plotted = True

            # Najlepsza próba wyróżniona ciągłą linią na pierwszym planie
            self.ax_best.plot(
                epochs,
                global_best_vals,
                label=f"Najlepsza próba (f={global_best_vals[-1]:.6g})",
                color="#d62728",
                linewidth=2.2,
                zorder=5,
            )
        else:
            self.ax_best.plot(
                epochs,
                global_best_vals,
                label=f"Najlepsza wartość f(x) (f={global_best_vals[-1]:.6g})",
                color="#d62728",
                linewidth=2.0,
            )

        self.ax_best.set_title(f"a) Wartość funkcji celu od kolejnej iteracji\n({func_name}, N={num_vars})", fontsize=10)
        self.ax_best.set_xlabel("Iteracja (Epoka)")
        self.ax_best.set_ylabel("Wartość funkcji celu f(x)")
        self.ax_best.grid(True, linestyle="--", alpha=0.5)
        self.ax_best.legend(loc="best", fontsize=9)
        self.figure_best.tight_layout(pad=2.5)
        self.canvas_best.draw()

        # Wykres 9b: Średnia wartość funkcji i odchylenie standardowe od kolejnej iteracji
        self.ax_stats.clear()
        self.ax_stats.plot(epochs, mean_vals, label="Średnia wartość funkcji", color="#2ca02c", linewidth=1.8)
        self.ax_stats.plot(epochs, std_vals, label="Odchylenie standardowe", color="#ff7f0e", linewidth=1.5, linestyle="--")
        lower = [m - s for m, s in zip(mean_vals, std_vals)]
        upper = [m + s for m, s in zip(mean_vals, std_vals)]
        self.ax_stats.fill_between(epochs, lower, upper, color="#2ca02c", alpha=0.15, label="Średnia ± odch. std")
        self.ax_stats.set_title(f"b) Średnia wartość funkcji i odchylenie standardowe od iteracji\n({func_name}, N={num_vars})", fontsize=10)
        self.ax_stats.set_xlabel("Iteracja (Epoka)")
        self.ax_stats.set_ylabel("Wartość")
        self.ax_stats.grid(True, linestyle="--", alpha=0.5)
        self.ax_stats.legend(loc="best", fontsize=9)
        self.figure_stats.tight_layout(pad=2.5)
        self.canvas_stats.draw()

    def export_csv_dialog(self):
        if self.last_ga is None or not self.last_ga.history:
            messagebox.showinfo("Informacja", "Brak wyników do zapisania. Uruchom najpierw algorytm.")
            return
        filepath = filedialog.asksaveasfilename(
            title="Zapisz historię iteracji do CSV",
            initialdir=str(self.results_dir),
            defaultextension=".csv",
            filetypes=[("Plik CSV", "*.csv"), ("Wszystkie pliki", "*.*")],
        )
        if filepath:
            saved = self.last_ga.save_history_csv(filepath, metadata=self.last_metadata)
            messagebox.showinfo("Zapisano CSV", f"Wyniki kolejnych iteracji zapisano w:\n{saved}")

    def export_json_dialog(self):
        if self.last_ga is None or not self.last_ga.history:
            messagebox.showinfo("Informacja", "Brak wyników do zapisania. Uruchom najpierw algorytm.")
            return
        filepath = filedialog.asksaveasfilename(
            title="Zapisz historię iteracji do JSON",
            initialdir=str(self.results_dir),
            defaultextension=".json",
            filetypes=[("Plik JSON", "*.json"), ("Wszystkie pliki", "*.*")],
        )
        if filepath:
            saved = self.last_ga.save_history_json(filepath, metadata=self.last_metadata)
            messagebox.showinfo("Zapisano JSON", f"Wyniki kolejnych iteracji zapisano w:\n{saved}")


def launch_gui():
    root = tk.Tk()
    app = GeneticAlgorithmGUI(root)
    root.mainloop()
    return app
