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


def _get_cec2014_opt_pos(func_name, num_variables):
    """Pobiera rzeczywiste współrzędne wektora optimum x* z instancji CEC2014 w opfunu."""
    cls = getattr(cec2014, func_name)
    supported_dims = [10, 20, 30, 50, 100]
    target_dim = next((d for d in supported_dims if d >= num_variables), 100)
    instance = cls(ndim=target_dim)
    return [round(float(v), 6) for v in instance.x_global[:num_variables]]


class FunctionRegistry:
    """Rejestr funkcji testowych dostępnych w aplikacji (benchmark_functions oraz opfunu CEC2014)."""

    FUNCTIONS = [
        BenchmarkFunctionSpec(
            key="bf_hypersphere",
            name="Hypersphere [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-5.0, 5.0),
            optimum_value_fn=lambda n: 0.0,
            optimum_pos_fn=lambda n: [0.0] * n,
            builder_fn=lambda n: _make_bf_evaluator("Hypersphere", n),
            description="Hypersphere: f(x) = sum(x_i^2). Zakres: [-5.0, 5.0]. Globalne minimum: 0.0 w punkcie [0.0, ..., 0.0].",
        ),
        BenchmarkFunctionSpec(
            key="bf_ackley",
            name="Ackley [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-32.768, 32.768),
            optimum_value_fn=lambda n: 4.440892098500626e-16,
            optimum_pos_fn=lambda n: [0.0] * n,
            builder_fn=lambda n: _make_bf_evaluator("Ackley", n),
            description="Ackley: zakres [-32.768, 32.768]. Globalne minimum: 4.440892098500626e-16 w punkcie [0.0, ..., 0.0].",
        ),
        BenchmarkFunctionSpec(
            key="bf_rastrigin",
            name="Rastrigin [benchmark_functions]",
            category="FunkcjeTestowe (benchmark_functions)",
            default_bounds=(-5.12, 5.12),
            optimum_value_fn=lambda n: 0.0,
            optimum_pos_fn=lambda n: [0.0] * n,
            builder_fn=lambda n: _make_bf_evaluator("Rastrigin", n),
            description="Rastrigin: f(x) = 10N + sum(x_i^2 - 10cos(2*pi*x_i)). Zakres: [-5.12, 5.12]. Globalne minimum: 0.0 w [0.0, ..., 0.0].",
        ),
        BenchmarkFunctionSpec(
            key="cec2014_f2",
            name="CEC2014 F2: Rotated Bent Cigar Function [opfunu]",
            category="CEC 2014 (opfunu)",
            default_bounds=(-100.0, 100.0),
            optimum_value_fn=lambda n: 200.0,
            optimum_pos_fn=lambda n: _get_cec2014_opt_pos("F22014", n),
            builder_fn=lambda n: _make_cec2014_evaluator("F22014", n),
            description="CEC2014 F2: Rotated Bent Cigar Function. Zakres: [-100.0, 100.0]. Globalne minimum f* = 200.0.",
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
