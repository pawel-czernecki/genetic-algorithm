import math

try:
    import benchmark_functions as bf
    HAS_BENCHMARK_FUNCTIONS = True
except ImportError:
    bf = None
    HAS_BENCHMARK_FUNCTIONS = False

try:
    import numpy as np
except ImportError:
    np = None

try:
    from opfunu.cec_based import cec2014
    HAS_OPFUNU = True
except ImportError:
    cec2014 = None
    HAS_OPFUNU = False


class BenchmarkFunctionSpec:
    """Obiektowa reprezentacja funkcji testowej (z biblioteki benchmark_functions lub opfunu)."""

    def __init__(
        self,
        key,
        name,
        category,
        default_bounds,
        optimum_value_fn,
        optimum_pos_fn,
        builder_fn,
        description="",
    ):
        self.key = key
        self.name = name
        self.category = category  # "FunkcjeTestowe (benchmark_functions)" lub "CEC 2014 (opfunu)"
        self.default_bounds = default_bounds  # (min, max)
        self._optimum_value_fn = optimum_value_fn
        self._optimum_pos_fn = optimum_pos_fn
        self._builder_fn = builder_fn
        self.description = description

    def get_optimum_info(self, num_variables):
        opt_val = self._optimum_value_fn(num_variables)
        opt_pos = self._optimum_pos_fn(num_variables)
        return opt_val, opt_pos

    def create_evaluator(self, num_variables):
        return self._builder_fn(num_variables)


def _make_bf_evaluator(cls_name, fallback_fn, num_variables):
    """Tworzy funkcję celu z pakietu benchmark_functions (lub fallback, gdy pakiet niedostępny)."""
    if HAS_BENCHMARK_FUNCTIONS and hasattr(bf, cls_name):
        cls = getattr(bf, cls_name)
        instance = cls(n_dimensions=num_variables)
        return lambda x: float(instance(list(x)))
    return fallback_fn


def _make_cec2014_evaluator(func_Name, fallback_fn, num_variables):
    """
    Tworzy funkcję celu z pakietu opfunu.cec_based.cec2014.
    Obsługuje dowolną liczbę zmiennych (np. 5, 10, 20, 27, 30):
    jeśli macierze rotacji CEC2014 w opfunu wymagają wymiaru z {2, 10, 20, 30, 50, 100},
    wektor jest bezpiecznie dopasowywany do najbliższego wspieranego wymiaru nadrzędnego.
    """
    if HAS_OPFUNU and hasattr(cec2014, func_Name):
        cls = getattr(cec2014, func_Name)
        supported_dims = [2, 10, 20, 30, 50, 100]
        try:
            instance = cls(ndim=num_variables)

            def _eval_direct(x):
                arr = np.asarray(x, dtype=float) if np is not None else list(x)
                return float(instance.evaluate(arr))

            # Szybki test poprawności wymiaru
            _eval_direct([0.0] * num_variables)
            return _eval_direct
        except Exception:
            target_dim = next((d for d in supported_dims if d >= num_variables), 100)
            instance = cls(ndim=target_dim)
            # Uzupełnienie pozostałych wymiarów wartościami punktu przesunięcia (x_shift) jeśli dostępne
            shift_pad = None
            if hasattr(instance, "f_shift") and instance.f_shift is not None:
                shift_pad = list(instance.f_shift[:target_dim])

            def _eval_adapted(x):
                vec = list(x)[:target_dim]
                if len(vec) < target_dim:
                    if shift_pad is not None:
                        vec.extend(shift_pad[len(vec) : target_dim])
                    else:
                        vec.extend([0.0] * (target_dim - len(vec)))
                arr = np.asarray(vec, dtype=float) if np is not None else vec
                return float(instance.evaluate(arr))

            return _eval_adapted

    return fallback_fn


# --- Definicje pomocnicze (używane gdy pakiety zewnętrzne nie są jeszcze zainstalowane) ---

def _fallback_hypersphere(x):
    return sum(v * v for v in x)


def _fallback_rastrigin(x):
    n = len(x)
    return 10.0 * n + sum(v * v - 10.0 * math.cos(2.0 * math.pi * v) for v in x)


def _fallback_rosenbrock(x):
    return sum(100.0 * (x[i + 1] - x[i] ** 2) ** 2 + (1.0 - x[i]) ** 2 for i in range(len(x) - 1))


def _fallback_ackley(x):
    n = len(x)
    sum_sq = sum(v * v for v in x)
    sum_cos = sum(math.cos(2.0 * math.pi * v) for v in x)
    return -20.0 * math.exp(-0.2 * math.sqrt(sum_sq / n)) - math.exp(sum_cos / n) + 20.0 + math.e


def _fallback_griewank(x):
    sum_sq = sum(v * v for v in x) / 4000.0
    prod_cos = 1.0
    for i, v in enumerate(x):
        prod_cos *= math.cos(v / math.sqrt(i + 1))
    return sum_sq - prod_cos + 1.0


def _fallback_schwefel(x):
    n = len(x)
    return 418.982887272433799807913601398 * n - sum(v * math.sin(math.sqrt(abs(v))) for v in x)


def _fallback_styblinski_tang(x):
    return 0.5 * sum(v**4 - 16.0 * v**2 + 5.0 * v for v in x)


def _fallback_cec2014_f1(x):
    # High Conditioned Elliptic Function (F1 CEC2014, f* = 100)
    n = len(x)
    if n == 1:
        return (x[0] ** 2) + 100.0
    return sum((10.0 ** (6.0 * i / (n - 1))) * (x[i] ** 2) for i in range(n)) + 100.0


def _fallback_cec2014_f2(x):
    # Bent Cigar Function (F2 CEC2014, f* = 200)
    return (x[0] ** 2) + (10.0**6) * sum(v * v for v in x[1:]) + 200.0


def _fallback_cec2014_f3(x):
    # Discus Function (F3 CEC2014, f* = 300)
    return (10.0**6) * (x[0] ** 2) + sum(v * v for v in x[1:]) + 300.0


def _fallback_cec2014_f8(x):
    # Shifted Rastrigin Function (F8 CEC2014, f* = 800)
    return _fallback_rastrigin(x) + 800.0


def _fallback_cec2014_f9(x):
    # Shifted Rotated Rastrigin Function (F9 CEC2014, f* = 900)
    return _fallback_rastrigin(x) + 900.0


class FunctionRegistry:
    """Rejestr funkcji testowych dostępnych w aplikacji."""

    FUNCTIONS = [
        BenchmarkFunctionSpec(
            key="bf_hypersphere",
            name="Hypersphere (Sphere) [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-5.12, 5.12),
            optimum_value_fn=lambda n: 0.0,
            optimum_pos_fn=lambda n: [0.0] * n,
            builder_fn=lambda n: _make_bf_evaluator("Hypersphere", _fallback_hypersphere, n),
            description="Funkcja sferyczna f(x) = sum(x_i^2). Globalne minimum f(0,...,0) = 0.",
        ),
        BenchmarkFunctionSpec(
            key="bf_rastrigin",
            name="Rastrigin [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-5.12, 5.12),
            optimum_value_fn=lambda n: 0.0,
            optimum_pos_fn=lambda n: [0.0] * n,
            builder_fn=lambda n: _make_bf_evaluator("Rastrigin", _fallback_rastrigin, n),
            description="Wielomodalna funkcja Rastrigina z licznymi minimami lokalnymi. Globalne minimum f(0,...,0) = 0.",
        ),
        BenchmarkFunctionSpec(
            key="bf_ackley",
            name="Ackley [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-32.768, 32.768),
            optimum_value_fn=lambda n: 0.0,
            optimum_pos_fn=lambda n: [0.0] * n,
            builder_fn=lambda n: _make_bf_evaluator("Ackley", _fallback_ackley, n),
            description="Funkcja Ackleya. Globalne minimum f(0,...,0) = 0.",
        ),
        BenchmarkFunctionSpec(
            key="bf_rosenbrock",
            name="Rosenbrock [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-5.0, 10.0),
            optimum_value_fn=lambda n: 0.0,
            optimum_pos_fn=lambda n: [1.0] * n,
            builder_fn=lambda n: _make_bf_evaluator("Rosenbrock", _fallback_rosenbrock, n),
            description="Dolina Rosenbrocka (funkcja bananowa). Globalne minimum f(1,...,1) = 0.",
        ),
        BenchmarkFunctionSpec(
            key="bf_griewank",
            name="Griewank [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-600.0, 600.0),
            optimum_value_fn=lambda n: 0.0,
            optimum_pos_fn=lambda n: [0.0] * n,
            builder_fn=lambda n: _make_bf_evaluator("Griewank", _fallback_griewank, n),
            description="Funkcja Griewanka. Globalne minimum f(0,...,0) = 0.",
        ),
        BenchmarkFunctionSpec(
            key="bf_schwefel",
            name="Schwefel [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-500.0, 500.0),
            optimum_value_fn=lambda n: 0.0,
            optimum_pos_fn=lambda n: [420.968746] * n,
            builder_fn=lambda n: _make_bf_evaluator("Schwefel", _fallback_schwefel, n),
            description="Funkcja Schwefela. Globalne minimum f(420.9687,...,420.9687) = 0.",
        ),
        BenchmarkFunctionSpec(
            key="bf_styblinski_tang",
            name="Styblinski-Tang [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-5.0, 5.0),
            optimum_value_fn=lambda n: -39.16616570377142 * n,
            optimum_pos_fn=lambda n: [-2.903534] * n,
            builder_fn=lambda n: _make_bf_evaluator("StyblinskiTang", _fallback_styblinski_tang, n),
            description="Funkcja Styblinskiego-Tanga. Minimum f(-2.9035,...,-2.9035) = -39.166165 * N.",
        ),
        BenchmarkFunctionSpec(
            key="cec2014_f1",
            name="CEC2014 F1: Rotated High Conditioned Elliptic [opfunu]",
            category="CEC 2014 (opfunu)",
            default_bounds=(-100.0, 100.0),
            optimum_value_fn=lambda n: 100.0,
            optimum_pos_fn=lambda n: "wektor przesunięcia o_1 (opfunu CEC2014)",
            builder_fn=lambda n: _make_cec2014_evaluator("F12014", _fallback_cec2014_f1, n),
            description="CEC2014 F1: Rotated High Conditioned Elliptic Function. Globalne minimum f* = 100.",
        ),
        BenchmarkFunctionSpec(
            key="cec2014_f2",
            name="CEC2014 F2: Rotated Bent Cigar [opfunu]",
            category="CEC 2014 (opfunu)",
            default_bounds=(-100.0, 100.0),
            optimum_value_fn=lambda n: 200.0,
            optimum_pos_fn=lambda n: "wektor przesunięcia o_2 (opfunu CEC2014)",
            builder_fn=lambda n: _make_cec2014_evaluator("F22014", _fallback_cec2014_f2, n),
            description="CEC2014 F2: Rotated Bent Cigar Function. Globalne minimum f* = 200.",
        ),
        BenchmarkFunctionSpec(
            key="cec2014_f3",
            name="CEC2014 F3: Rotated Discus [opfunu]",
            category="CEC 2014 (opfunu)",
            default_bounds=(-100.0, 100.0),
            optimum_value_fn=lambda n: 300.0,
            optimum_pos_fn=lambda n: "wektor przesunięcia o_3 (opfunu CEC2014)",
            builder_fn=lambda n: _make_cec2014_evaluator("F32014", _fallback_cec2014_f3, n),
            description="CEC2014 F3: Rotated Discus Function. Globalne minimum f* = 300.",
        ),
        BenchmarkFunctionSpec(
            key="cec2014_f8",
            name="CEC2014 F8: Shifted Rastrigin [opfunu]",
            category="CEC 2014 (opfunu)",
            default_bounds=(-100.0, 100.0),
            optimum_value_fn=lambda n: 800.0,
            optimum_pos_fn=lambda n: "wektor przesunięcia o_8 (opfunu CEC2014)",
            builder_fn=lambda n: _make_cec2014_evaluator("F82014", _fallback_cec2014_f8, n),
            description="CEC2014 F8: Shifted Rastrigin's Function. Globalne minimum f* = 800.",
        ),
        BenchmarkFunctionSpec(
            key="cec2014_f9",
            name="CEC2014 F9: Shifted & Rotated Rastrigin [opfunu]",
            category="CEC 2014 (opfunu)",
            default_bounds=(-100.0, 100.0),
            optimum_value_fn=lambda n: 900.0,
            optimum_pos_fn=lambda n: "wektor przesunięcia o_9 (opfunu CEC2014)",
            builder_fn=lambda n: _make_cec2014_evaluator("F92014", _fallback_cec2014_f9, n),
            description="CEC2014 F9: Shifted and Rotated Rastrigin's Function. Globalne minimum f* = 900.",
        ),
    ]

    @classmethod
    def get_all(cls):
        return list(cls.FUNCTIONS)

    @classmethod
    def get_by_name(cls, name):
        for spec in cls.FUNCTIONS:
            if spec.name == name or spec.key == name:
                return spec
        return cls.FUNCTIONS[0]

