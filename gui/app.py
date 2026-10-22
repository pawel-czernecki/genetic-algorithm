from datetime import datetime
from pathlib import Path
import statistics
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from engine.algorithm import GeneticAlgorithm
from engine.crossover import Crossover
from engine.functions import FunctionRegistry, HAS_BENCHMARK_FUNCTIONS, HAS_OPFUNU
from engine.mutation import Mutation
from engine.selection import Selection

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class GeneticAlgorithmGUI:
    """Główna klasa interfejsu graficznego (Tkinter/ttk) dla klasycznego algorytmu genetycznego."""

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

        self.var_precision_mode = tk.StringVar(value="bits")  # "bits" lub "decimal"
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
        self.var_mut_prob = tk.DoubleVar(value=0.05)

        self.var_inv_prob = tk.DoubleVar(value=0.05)

        self.var_elite_mode = tk.StringVar(value="percent")  # "percent" lub "count"
        self.var_elite_value = tk.DoubleVar(value=10.0)  # 10% domyślnie

        self.var_auto_save = tk.BooleanVar(value=True)
        self.var_status = tk.StringVar(value="Gotowy do uruchomienia.")
        self.var_exec_time = tk.StringVar(value="0.0000 s")

    def _build_layout(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Panel lewy: konfiguracja
        left_container = ttk.Frame(main_pane, width=430)
        main_pane.add(left_container, weight=0)

        # Panel prawy: wyniki, czas, wykresy i tabela epok
        right_container = ttk.Frame(main_pane)
        main_pane.add(right_container, weight=1)

        self._build_config_panel(left_container)
        self._build_results_panel(right_container)

    def _build_config_panel(self, parent):
        # Sekcja 1: Funkcja celu i zmienne
        func_frame = ttk.LabelFrame(parent, text="1. Funkcja celu i przestrzeń poszukiwań", padding=8)
        func_frame.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(func_frame, text="Funkcja testowa:").grid(row=0, column=0, sticky=tk.W, pady=2)
        func_names = [f.name for f in FunctionRegistry.get_all()]
        cb_func = ttk.Combobox(func_frame, textvariable=self.var_function, values=func_names, state="readonly", width=38)
        cb_func.grid(row=0, column=1, columnspan=3, sticky=tk.EW, pady=2)
        cb_func.bind("<<ComboboxSelected>>", lambda _e: self._on_function_change())

        self.lbl_func_desc = ttk.Label(func_frame, text="", wraplength=390, foreground="#333333", font=("TkDefaultFont", 8))
        self.lbl_func_desc.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(2, 4))

        ttk.Label(func_frame, text="Typ optymalizacji:").grid(row=2, column=0, sticky=tk.W, pady=2)
        opt_sub = ttk.Frame(func_frame)
        opt_sub.grid(row=2, column=1, columnspan=3, sticky=tk.W)
        ttk.Radiobutton(opt_sub, text="Minimalizacja (min)", variable=self.var_opt_type, value="min").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(opt_sub, text="Maksymalizacja (max)", variable=self.var_opt_type, value="max").pack(side=tk.LEFT)

        ttk.Label(func_frame, text="Liczba zmiennych (N):").grid(row=3, column=0, sticky=tk.W, pady=2)
        vars_sub = ttk.Frame(func_frame)
        vars_sub.grid(row=3, column=1, columnspan=3, sticky=tk.W)
        ttk.Spinbox(vars_sub, from_=1, to=200, textvariable=self.var_num_vars, width=8).pack(side=tk.LEFT)
        for preset in (2, 5, 10, 20, 27, 30):
            ttk.Button(
                vars_sub,
                text=str(preset),
                width=3,
                command=lambda v=preset: self.var_num_vars.set(v),
            ).pack(side=tk.LEFT, padx=1)

        ttk.Label(func_frame, text="Przedział [min, max]:").grid(row=4, column=0, sticky=tk.W, pady=2)
        bounds_sub = ttk.Frame(func_frame)
        bounds_sub.grid(row=4, column=1, columnspan=3, sticky=tk.W)
        ttk.Entry(bounds_sub, textvariable=self.var_bound_min, width=10).pack(side=tk.LEFT)
        ttk.Label(bounds_sub, text=" do ").pack(side=tk.LEFT)
        ttk.Entry(bounds_sub, textvariable=self.var_bound_max, width=10).pack(side=tk.LEFT)

        func_frame.columnconfigure(1, weight=1)

        # Sekcja 2: Chromosom i populacja
        pop_frame = ttk.LabelFrame(parent, text="2. Reprezentacja binarna i populacja", padding=8)
        pop_frame.pack(fill=tk.X, pady=(0, 6))

        ttk.Radiobutton(
            pop_frame,
            text="Liczba bitów na zmienną:",
            variable=self.var_precision_mode,
            value="bits",
        ).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(pop_frame, from_=2, to=64, textvariable=self.var_bit_precision, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)

        ttk.Radiobutton(
            pop_frame,
            text="Dokładność dziesiętna d (10^-d):",
            variable=self.var_precision_mode,
            value="decimal",
        ).grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(pop_frame, from_=1, to=12, textvariable=self.var_decimal_precision, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)

        ttk.Label(pop_frame, text="Wielkość populacji:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(pop_frame, from_=4, to=5000, increment=10, textvariable=self.var_pop_size, width=10).grid(row=2, column=1, sticky=tk.W, pady=2)

        ttk.Label(pop_frame, text="Liczba epok (iteracji):").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(pop_frame, from_=1, to=10000, increment=50, textvariable=self.var_epochs, width=10).grid(row=3, column=1, sticky=tk.W, pady=2)

        # Sekcja 3: Operatory genetyczne
        op_frame = ttk.LabelFrame(parent, text="3. Selekcja, krzyżowanie, mutacja, inwersja", padding=8)
        op_frame.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(op_frame, text="Metoda selekcji:").grid(row=0, column=0, sticky=tk.W, pady=2)
        cb_sel = ttk.Combobox(
            op_frame,
            textvariable=self.var_selection,
            values=list(self.SELECTION_MAP.keys()),
            state="readonly",
            width=25,
        )
        cb_sel.grid(row=0, column=1, sticky=tk.EW, pady=2)
        cb_sel.bind("<<ComboboxSelected>>", lambda _e: self._on_selection_change())

        self.lbl_sel_param = ttk.Label(op_frame, text="Rozmiar turnieju (k):")
        self.lbl_sel_param.grid(row=1, column=0, sticky=tk.W, pady=2)
        self.ent_sel_param = ttk.Entry(op_frame, textvariable=self.var_selection_param, width=10)
        self.ent_sel_param.grid(row=1, column=1, sticky=tk.W, pady=2)

        ttk.Label(op_frame, text="Metoda krzyżowania:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(
            op_frame,
            textvariable=self.var_crossover,
            values=list(self.CROSSOVER_MAP.keys()),
            state="readonly",
            width=25,
        ).grid(row=2, column=1, sticky=tk.EW, pady=2)

        ttk.Label(op_frame, text="Prawdop. krzyżowania (p_c):").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(op_frame, from_=0.0, to=1.0, increment=0.05, textvariable=self.var_cross_prob, width=10).grid(row=3, column=1, sticky=tk.W, pady=2)

        ttk.Label(op_frame, text="Metoda mutacji:").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(
            op_frame,
            textvariable=self.var_mutation,
            values=list(self.MUTATION_MAP.keys()),
            state="readonly",
            width=25,
        ).grid(row=4, column=1, sticky=tk.EW, pady=2)

        ttk.Label(op_frame, text="Prawdop. mutacji (p_m):").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(op_frame, from_=0.0, to=1.0, increment=0.01, textvariable=self.var_mut_prob, width=10).grid(row=5, column=1, sticky=tk.W, pady=2)

        ttk.Label(op_frame, text="Prawdop. inwersji (p_i):").grid(row=6, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(op_frame, from_=0.0, to=1.0, increment=0.01, textvariable=self.var_inv_prob, width=10).grid(row=6, column=1, sticky=tk.W, pady=2)

        op_frame.columnconfigure(1, weight=1)

        # Sekcja 4: Strategia elitarna i eksperyment wielokrotny
        elite_frame = ttk.LabelFrame(parent, text="4. Strategia elitarna i uruchomienia", padding=8)
        elite_frame.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(elite_frame, text="Tryb elitaryzmu:").grid(row=0, column=0, sticky=tk.W, pady=2)
        elite_sub = ttk.Frame(elite_frame)
        elite_sub.grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(elite_sub, text="% populacji", variable=self.var_elite_mode, value="percent").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Radiobutton(elite_sub, text="Liczba osobników", variable=self.var_elite_mode, value="count").pack(side=tk.LEFT)

        ttk.Label(elite_frame, text="Wartość elity (% lub szt.):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(elite_frame, from_=0, to=100, increment=1, textvariable=self.var_elite_value, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)

        ttk.Label(elite_frame, text="Liczba powtórzeń (np. 1 lub 10):").grid(row=2, column=0, sticky=tk.W, pady=2)
        runs_sub = ttk.Frame(elite_frame)
        runs_sub.grid(row=2, column=1, sticky=tk.W)
        ttk.Spinbox(runs_sub, from_=1, to=50, textvariable=self.var_num_runs, width=8).pack(side=tk.LEFT)
        ttk.Button(runs_sub, text="10x (Sprawozdanie)", command=lambda: self.var_num_runs.set(10)).pack(side=tk.LEFT, padx=4)

        ttk.Checkbutton(
            elite_frame,
            text="Automatycznie zapisuj iteracje do CSV i JSON (results/)",
            variable=self.var_auto_save,
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(4, 2))

        # Przyciski sterujące
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=4)

        self.btn_run = ttk.Button(btn_frame, text="▶ Uruchom algorytm", command=self.start_algorithm)
        self.btn_run.pack(fill=tk.X, pady=2, ipady=4)

        export_sub = ttk.Frame(btn_frame)
        export_sub.pack(fill=tk.X, pady=2)
        ttk.Button(export_sub, text="Zapisz wyniki CSV...", command=self.export_csv_dialog).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(export_sub, text="Zapisz wyniki JSON...", command=self.export_json_dialog).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        self.progress = ttk.Progressbar(parent, orient=tk.HORIZONTAL, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(4, 2))
        ttk.Label(parent, textvariable=self.var_status, foreground="#005580").pack(anchor=tk.W)

    def _build_results_panel(self, parent):
        # Pasek podsumowania i czasu wykonania
        summary_frame = ttk.LabelFrame(parent, text="Podsumowanie obliczeń i wyniki", padding=8)
        summary_frame.pack(fill=tk.X, pady=(0, 6))

        time_box = ttk.Frame(summary_frame)
        time_box.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(time_box, text="Czas wykonywanych obliczeń:", font=("TkDefaultFont", 10, "bold")).pack(side=tk.LEFT)
        ttk.Label(time_box, textvariable=self.var_exec_time, font=("TkDefaultFont", 11, "bold"), foreground="#b30000").pack(side=tk.LEFT, padx=8)

        pkg_status = (
            f"Biblioteki funkcji: benchmark_functions={'TAK' if HAS_BENCHMARK_FUNCTIONS else 'FALLBACK'}, "
            f"opfunu(CEC2014)={'TAK' if HAS_OPFUNU else 'FALLBACK'}"
        )
        ttk.Label(time_box, text=pkg_status, foreground="#555555", font=("TkDefaultFont", 8)).pack(side=tk.RIGHT)

        self.txt_summary = tk.Text(summary_frame, height=6, wrap=tk.WORD, font=("Consolas", 9))
        self.txt_summary.pack(fill=tk.X)
        self.txt_summary.insert(tk.END, "Skonfiguruj parametry po lewej stronie i kliknij 'Uruchom algorytm'.")
        self.txt_summary.configure(state=tk.DISABLED)

        # Zakładki z wykresami oraz tabelą iteracji
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_plots = ttk.Frame(self.notebook)
        self.tab_table = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_plots, text="Wykresy (pkt 9a i 9b)")
        self.notebook.add(self.tab_table, text="Tabela kolejnych iteracji (pkt 10)")

        self._build_plots_area(self.tab_plots)
        self._build_table_area(self.tab_table)

    def _build_plots_area(self, parent):
        top_bar = ttk.Frame(parent)
        top_bar.pack(fill=tk.X, padx=6, pady=4)
        ttk.Label(
            top_bar,
            text="a) Wartość funkcji celu od kolejnej iteracji   |   b) Średnia wartość funkcji i odchylenie standardowe od iteracji",
            font=("TkDefaultFont", 9, "bold"),
        ).pack(side=tk.LEFT)
        if HAS_MATPLOTLIB:
            ttk.Button(top_bar, text="Zapisz wykresy do PNG...", command=self.save_plots_png).pack(side=tk.RIGHT)

        if HAS_MATPLOTLIB:
            self.figure = Figure(figsize=(9.5, 5.2), dpi=100)
            self.ax_best = self.figure.add_subplot(1, 2, 1)
            self.ax_stats = self.figure.add_subplot(1, 2, 2)
            self.figure.tight_layout(pad=3.0)

            self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar_frame = ttk.Frame(parent)
            toolbar_frame.pack(fill=tk.X)
            toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            toolbar.update()
        else:
            # Wbudowany renderer wykresów na wypadek braku biblioteki matplotlib
            self.fallback_canvas = tk.Canvas(parent, bg="white")
            self.fallback_canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
            self.fallback_canvas.bind("<Configure>", lambda _e: self._draw_fallback_plots())

    def _build_table_area(self, parent):
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

    def _set_summary_text(self, text: str):
        self.txt_summary.configure(state=tk.NORMAL)
        self.txt_summary.delete("1.0", tk.END)
        self.txt_summary.insert(tk.END, text)
        self.txt_summary.configure(state=tk.DISABLED)

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
            if self.var_auto_save.get() and best_ga is not None:
                csv_path = self.results_dir / f"wyniki_{spec.key}_N{num_vars}_{timestamp}.csv"
                json_path = self.results_dir / f"wyniki_{spec.key}_N{num_vars}_{timestamp}.json"
                best_ga.save_history_csv(csv_path, metadata=self.last_metadata)
                best_ga.save_history_json(json_path, metadata=self.last_metadata)
                saved_files = [csv_path.name, json_path.name]

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

    def _on_run_complete(self, spec, best_ga, runs_results, opt_real_val, opt_real_pos, error_val, saved_files):
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
            self.var_exec_time.set(f"{mean_time:.4f} s (średni z {num_runs} uruch., łącznie {total_time:.4f} s)")

        best_ind = best_ga.best_individual or Selection.best(best_ga.population, 1, best_ga.opt_type)[0]
        decoded_vars = best_ind.decode()
        vars_preview = ", ".join(f"x{i+1}={v:.5f}" for i, v in enumerate(decoded_vars[:8]))
        if len(decoded_vars) > 8:
            vars_preview += f", ... (łącznie N={len(decoded_vars)} zmiennych)"

        err_str = f"{error_val:.6f}" if error_val is not None else "n/d"
        lines = [
            f"Funkcja: {spec.name} | Zmienne N={best_ga.num_variables} | Bity/zmienną: {best_ga.bit_precision} (dł. chromosomu: {best_ga.num_variables * best_ga.bit_precision} bitów)",
            f"Rzeczywiste optimum f* = {opt_real_val}  |  Osiągnięte optimum f_AG = {best_ind.fitness:.6f}  |  Błąd |f_AG - f*| = {err_str}",
            f"Najlepsze znalezione argumenty: [{vars_preview}]",
        ]
        if num_runs > 1:
            mean_s = statistics.fmean(scores)
            std_s = statistics.pstdev(scores)
            best_s = min(scores) if best_ga.opt_type == "min" else max(scores)
            worst_s = max(scores) if best_ga.opt_type == "min" else min(scores)
            lines.append(
                f"Statystyki z {num_runs} uruchomień -> Średnia: {mean_s:.6f} | Odch. std: {std_s:.6f} | "
                f"Najlepszy: {best_s:.6f} | Najgorszy: {worst_s:.6f} | Śr. czas: {mean_time:.4f} s"
            )
        if saved_files:
            lines.append(f"Zapisano pliki w results/: {', '.join(saved_files)}")

        self._set_summary_text("\n".join(lines))
        self._populate_table(best_ga.history)
        self._update_plots(best_ga.history, spec.name, best_ga.num_variables)
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

    def _update_plots(self, history, func_name, num_vars):
        if not history:
            return
        if HAS_MATPLOTLIB:
            epochs = [h["epoch"] for h in history]
            best_vals = [h["best_fitness"] for h in history]
            global_best_vals = [h["global_best_fitness"] for h in history]
            mean_vals = [h["mean_fitness"] for h in history]
            std_vals = [h["std_fitness"] for h in history]

            # Wykres 9a: Wartość funkcji od kolejnej iteracji
            self.ax_best.clear()
            self.ax_best.plot(epochs, best_vals, label="Najlepszy w epoce", color="#1f77b4", linewidth=1.3, alpha=0.8)
            self.ax_best.plot(epochs, global_best_vals, label="Najlepszy globalnie", color="#d62728", linewidth=2.0)
            self.ax_best.set_title(f"a) Wartość funkcji celu od iteracji\n({func_name}, N={num_vars})", fontsize=9.5)
            self.ax_best.set_xlabel("Iteracja (Epoka)")
            self.ax_best.set_ylabel("Wartość funkcji celu f(x)")
            self.ax_best.grid(True, linestyle="--", alpha=0.5)
            self.ax_best.legend(loc="best", fontsize=8)

            # Wykres 9b: Średnia wartość funkcji i odchylenie standardowe od kolejnej iteracji
            self.ax_stats.clear()
            self.ax_stats.plot(epochs, mean_vals, label="Średnia wartość funkcji", color="#2ca02c", linewidth=1.8)
            self.ax_stats.plot(epochs, std_vals, label="Odchylenie standardowe", color="#ff7f0e", linewidth=1.5, linestyle="--")
            lower = [m - s for m, s in zip(mean_vals, std_vals)]
            upper = [m + s for m, s in zip(mean_vals, std_vals)]
            self.ax_stats.fill_between(epochs, lower, upper, color="#2ca02c", alpha=0.15, label="Średnia ± odch. std")
            self.ax_stats.set_title(f"b) Średnia wartość funkcji i odch. std\n({func_name}, N={num_vars})", fontsize=9.5)
            self.ax_stats.set_xlabel("Iteracja (Epoka)")
            self.ax_stats.set_ylabel("Wartość")
            self.ax_stats.grid(True, linestyle="--", alpha=0.5)
            self.ax_stats.legend(loc="best", fontsize=8)

            self.figure.tight_layout(pad=2.5)
            self.canvas.draw()
        else:
            self._draw_fallback_plots()

    def _draw_fallback_plots(self):
        if HAS_MATPLOTLIB or not hasattr(self, "fallback_canvas"):
            return
        c = self.fallback_canvas
        c.delete("all")
        if not self.last_ga or not self.last_ga.history:
            c.create_text(300, 150, text="Uruchom algorytm, aby wygenerować wykresy.", font=("TkDefaultFont", 11))
            return

        w = max(600, c.winfo_width())
        h = max(320, c.winfo_height())
        mid = w // 2
        history = self.last_ga.history
        epochs = [r["epoch"] for r in history]

        self._draw_single_canvas_chart(
            c,
            x0=45,
            y0=30,
            x1=mid - 20,
            y1=h - 40,
            epochs=epochs,
            series=[
                ([r["best_fitness"] for r in history], "#1f77b4", "Najlepszy w epoce"),
                ([r["global_best_fitness"] for r in history], "#d62728", "Najlepszy globalnie"),
            ],
            title="a) Wartość funkcji celu od kolejnej iteracji",
        )
        self._draw_single_canvas_chart(
            c,
            x0=mid + 35,
            y0=30,
            x1=w - 25,
            y1=h - 40,
            epochs=epochs,
            series=[
                ([r["mean_fitness"] for r in history], "#2ca02c", "Średnia funkcji"),
                ([r["std_fitness"] for r in history], "#ff7f0e", "Odchylenie std"),
            ],
            title="b) Średnia i odchylenie standardowe od iteracji",
        )

    def _draw_single_canvas_chart(self, canvas, x0, y0, x1, y1, epochs, series, title):
        canvas.create_rectangle(x0, y0, x1, y1, outline="#888888", fill="#fafafa")
        canvas.create_text((x0 + x1) // 2, y0 - 12, text=title, font=("TkDefaultFont", 9, "bold"))

        all_vals = [v for vals, _, _ in series for v in vals]
        min_v, max_v = min(all_vals), max(all_vals)
        if abs(max_v - min_v) < 1e-12:
            max_v = min_v + 1.0

        n = len(epochs)
        for idx, (vals, color, label) in enumerate(series):
            pts = []
            for i, val in enumerate(vals):
                px = x0 + (x1 - x0) * (i / max(1, n - 1))
                py = y1 - (y1 - y0) * ((val - min_v) / (max_v - min_v))
                pts.extend((px, py))
            if len(pts) >= 4:
                canvas.create_line(*pts, fill=color, width=2)
            canvas.create_text(x1 - 10, y0 + 15 + idx * 16, text=label, fill=color, anchor=tk.E, font=("TkDefaultFont", 8, "bold"))

        canvas.create_text(x0, y0 + 6, text=f"{max_v:.2f}", anchor=tk.E, font=("TkDefaultFont", 7))
        canvas.create_text(x0, y1 - 6, text=f"{min_v:.2f}", anchor=tk.E, font=("TkDefaultFont", 7))
        canvas.create_text((x0 + x1) // 2, y1 + 15, text=f"Iteracje (1 .. {epochs[-1]})", font=("TkDefaultFont", 8))

    def save_plots_png(self):
        if not HAS_MATPLOTLIB or self.last_ga is None:
            messagebox.showinfo("Informacja", "Najpierw uruchom algorytm, aby zapisać wykres.")
            return
        filepath = filedialog.asksaveasfilename(
            title="Zapisz wykresy do pliku PNG",
            initialdir=str(self.results_dir),
            defaultextension=".png",
            filetypes=[("Obraz PNG", "*.png"), ("Wszystkie pliki", "*.*")],
        )
        if filepath:
            self.figure.savefig(filepath, dpi=150, bbox_inches="tight")
            messagebox.showinfo("Zapisano", f"Wykresy zostały zapisane do:\n{filepath}")

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

