import benchmark_functions as bf
import numpy as np
from opfunu.cec_based import cec2014


class BenchmarkFunctionSpec:
    """Obiektowa reprezentacja funkcji testowej z bibliotek benchmark_functions oraz opfunu."""

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
        self.category = category
        self.default_bounds = default_bounds
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


def _make_bf_evaluator(cls_name, num_variables):
    """Tworzy funkcję celu bezpośrednio z biblioteki benchmark_functions."""
    cls = getattr(bf, cls_name)
    instance = cls(n_dimensions=num_variables)
    return lambda x: float(instance(list(x)))


def _make_cec2014_evaluator(func_name, num_variables):
    """
    Tworzy funkcję celu bezpośrednio z biblioteki opfunu.cec_based.cec2014.
    Macierze rotacji CEC2014 w opfunu są zdefiniowane dla wymiarów {10, 20, 30, 50, 100};
    dla innych wymiarów (np. N=5 lub N=27) wektor wejściowy jest dopasowywany do najbliższego
    wspieranego wymiaru nadrzędnego z opfunu.
    """
    cls = getattr(cec2014, func_name)
    supported_dims = [10, 20, 30, 50, 100]
    if num_variables in supported_dims:
        instance = cls(ndim=num_variables)
        return lambda x: float(instance.evaluate(np.asarray(x, dtype=float)))

    target_dim = next((d for d in supported_dims if d >= num_variables), 100)
    instance = cls(ndim=target_dim)
    shift_pad = (
        list(instance.f_shift[:target_dim])
        if getattr(instance, "f_shift", None) is not None
        else [0.0] * target_dim
    )

    def _eval_adapted(x):
        vec = list(x)[:target_dim]
        if len(vec) < target_dim:
            vec.extend(shift_pad[len(vec) : target_dim])
        return float(instance.evaluate(np.asarray(vec, dtype=float)))

    return _eval_adapted


class FunctionRegistry:
    """Rejestr funkcji testowych dostępnych w aplikacji (benchmark_functions oraz opfunu CEC2014)."""

    FUNCTIONS = [
        BenchmarkFunctionSpec(
            key="bf_hypersphere",
            name="Hypersphere (Sphere) [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-5.12, 5.12),
            optimum_value_fn=lambda n: 0.0,
            optimum_pos_fn=lambda n: [0.0] * n,
            builder_fn=lambda n: _make_bf_evaluator("Hypersphere", n),
            description="Funkcja sferyczna f(x) = sum(x_i^2). Globalne minimum f(0,...,0) = 0.",
        ),
        BenchmarkFunctionSpec(
            key="bf_rastrigin",
            name="Rastrigin [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-5.12, 5.12),
            optimum_value_fn=lambda n: 0.0,
            optimum_pos_fn=lambda n: [0.0] * n,
            builder_fn=lambda n: _make_bf_evaluator("Rastrigin", n),
            description="Wielomodalna funkcja Rastrigina z licznymi minimami lokalnymi. Globalne minimum f(0,...,0) = 0.",
        ),
        BenchmarkFunctionSpec(
            key="bf_ackley",
            name="Ackley [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-32.768, 32.768),
            optimum_value_fn=lambda n: 0.0,
            optimum_pos_fn=lambda n: [0.0] * n,
            builder_fn=lambda n: _make_bf_evaluator("Ackley", n),
            description="Funkcja Ackleya. Globalne minimum f(0,...,0) = 0.",
        ),
        BenchmarkFunctionSpec(
            key="bf_rosenbrock",
            name="Rosenbrock [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-5.0, 10.0),
            optimum_value_fn=lambda n: 0.0,
            optimum_pos_fn=lambda n: [1.0] * n,
            builder_fn=lambda n: _make_bf_evaluator("Rosenbrock", n),
            description="Dolina Rosenbrocka (funkcja bananowa). Globalne minimum f(1,...,1) = 0.",
        ),
        BenchmarkFunctionSpec(
            key="bf_griewank",
            name="Griewank [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-600.0, 600.0),
            optimum_value_fn=lambda n: 0.0,
            optimum_pos_fn=lambda n: [0.0] * n,
            builder_fn=lambda n: _make_bf_evaluator("Griewank", n),
            description="Funkcja Griewanka. Globalne minimum f(0,...,0) = 0.",
        ),
        BenchmarkFunctionSpec(
            key="bf_schwefel",
            name="Schwefel [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-500.0, 500.0),
            optimum_value_fn=lambda n: 0.0,
            optimum_pos_fn=lambda n: [420.968746] * n,
            builder_fn=lambda n: _make_bf_evaluator("Schwefel", n),
            description="Funkcja Schwefela. Globalne minimum f(420.9687,...,420.9687) = 0.",
        ),
        BenchmarkFunctionSpec(
            key="bf_styblinski_tang",
            name="Styblinski-Tang [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-5.0, 5.0),
            optimum_value_fn=lambda n: -39.16616570377142 * n,
            optimum_pos_fn=lambda n: [-2.903534] * n,
            builder_fn=lambda n: _make_bf_evaluator("StyblinskiTang", n),
            description="Funkcja Styblinskiego-Tanga. Minimum f(-2.9035,...,-2.9035) = -39.166165 * N.",
        ),
        BenchmarkFunctionSpec(
            key="cec2014_f1",
            name="CEC2014 F1: Rotated High Conditioned Elliptic [opfunu]",
            category="CEC 2014 (opfunu)",
            default_bounds=(-100.0, 100.0),
            optimum_value_fn=lambda n: 100.0,
            optimum_pos_fn=lambda n: "wektor przesunięcia o_1 (opfunu CEC2014)",
            builder_fn=lambda n: _make_cec2014_evaluator("F12014", n),
            description="CEC2014 F1: Rotated High Conditioned Elliptic Function. Globalne minimum f* = 100.",
        ),
        BenchmarkFunctionSpec(
            key="cec2014_f2",
            name="CEC2014 F2: Rotated Bent Cigar [opfunu]",
            category="CEC 2014 (opfunu)",
            default_bounds=(-100.0, 100.0),
            optimum_value_fn=lambda n: 200.0,
            optimum_pos_fn=lambda n: "wektor przesunięcia o_2 (opfunu CEC2014)",
            builder_fn=lambda n: _make_cec2014_evaluator("F22014", n),
            description="CEC2014 F2: Rotated Bent Cigar Function. Globalne minimum f* = 200.",
        ),
        BenchmarkFunctionSpec(
            key="cec2014_f3",
            name="CEC2014 F3: Rotated Discus [opfunu]",
            category="CEC 2014 (opfunu)",
            default_bounds=(-100.0, 100.0),
            optimum_value_fn=lambda n: 300.0,
            optimum_pos_fn=lambda n: "wektor przesunięcia o_3 (opfunu CEC2014)",
            builder_fn=lambda n: _make_cec2014_evaluator("F32014", n),
            description="CEC2014 F3: Rotated Discus Function. Globalne minimum f* = 300.",
        ),
        BenchmarkFunctionSpec(
            key="cec2014_f8",
            name="CEC2014 F8: Shifted Rastrigin [opfunu]",
            category="CEC 2014 (opfunu)",
            default_bounds=(-100.0, 100.0),
            optimum_value_fn=lambda n: 800.0,
            optimum_pos_fn=lambda n: "wektor przesunięcia o_8 (opfunu CEC2014)",
            builder_fn=lambda n: _make_cec2014_evaluator("F82014", n),
            description="CEC2014 F8: Shifted Rastrigin's Function. Globalne minimum f* = 800.",
        ),
        BenchmarkFunctionSpec(
            key="cec2014_f9",
            name="CEC2014 F9: Shifted & Rotated Rastrigin [opfunu]",
            category="CEC 2014 (opfunu)",
            default_bounds=(-100.0, 100.0),
            optimum_value_fn=lambda n: 900.0,
            optimum_pos_fn=lambda n: "wektor przesunięcia o_9 (opfunu CEC2014)",
            builder_fn=lambda n: _make_cec2014_evaluator("F92014", n),
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
