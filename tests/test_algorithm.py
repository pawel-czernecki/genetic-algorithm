import json
import os
from pathlib import Path
import random
import tempfile
import unittest

from engine.algorithm import GeneticAlgorithm
from engine.chromosome import Chromosome
from engine.crossover import Crossover
from engine.functions import FunctionRegistry
from engine.mutation import Mutation
from engine.selection import Selection


class TestGeneticAlgorithmProject(unittest.TestCase):
    def test_variable_dimensions_5_10_20_27(self):
        """Dowolna liczba zmiennych (5, 10, 20, 27) oraz dokładność bitowa i dziesiętna."""
        spec = FunctionRegistry.get_by_name("bf_hypersphere")
        for n_vars in (5, 10, 20, 27):
            ga = GeneticAlgorithm(
                pop_size=20,
                epochs=5,
                num_variables=n_vars,
                bit_precision=12,
                bounds=spec.default_bounds,
                fitness_func=spec.create_evaluator(n_vars),
                opt_type="min",
                elite_percent=0.1,
            )
            history = ga.run(verbose=False)
            self.assertEqual(len(history), 5)
            self.assertEqual(len(history[-1]["best_variables"]), n_vars)

        # Test dokładności dziesiętnej d=4
        ch = Chromosome(num_variables=5, representation="binary", bounds=(-10, 10), decimal_precision=4)
        self.assertEqual(ch.bit_precision, 18)  # ceil(log2(20 * 10^4 + 1)) = 18

    def test_selection_methods(self):
        """Selekcja najlepszych, najgorszych, ruletki i turniejowa + parametry."""
        spec = FunctionRegistry.get_by_name("bf_rastrigin")
        for sel_method, param in [
            (Selection.best, 0.4),
            (Selection.worst, 0.4),
            (Selection.roulette, None),
            (Selection.tournament, 4),
        ]:
            ga = GeneticAlgorithm(
                pop_size=20,
                epochs=5,
                num_variables=5,
                bit_precision=10,
                bounds=spec.default_bounds,
                fitness_func=spec.create_evaluator(5),
                opt_type="min",
            )
            history = ga.run(selection_method=sel_method, selection_param=param, verbose=False)
            self.assertEqual(len(history), 5)

    def test_crossover_methods(self):
        """Krzyżowanie jednopunktowe, dwupunktowe, jednorodne, ziarniste."""
        p1 = Chromosome(4, 8, (-5, 5), genes=[0] * 32)
        p2 = Chromosome(4, 8, (-5, 5), genes=[1] * 32)

        for method in (
            Crossover.onepoint_crossover,
            Crossover.twopoint_crossover,
            Crossover.uniform_crossover,
            Crossover.granular,
        ):
            # Prawdopodobieństwo 0.0 -> brak zmian, brak wyjątków (dawniej UnboundLocalError w twopoint)
            c1, c2 = method(p1, p2, 0.0)
            self.assertEqual(c1.genes, [0] * 32)
            self.assertEqual(c2.genes, [1] * 32)

            # Prawdopodobieństwo 1.0 -> wymiana genów z zachowaniem sumy kontrolnej bitów
            c1, c2 = method(p1, p2, 1.0)
            for b1, b2 in zip(c1.genes, c2.genes):
                self.assertEqual(b1 + b2, 1, f"Błąd wymiany bitów w metodzie {method.__name__}")

    def test_mutation_and_inversion(self):
        """Mutacja brzegowa, jedno- i dwupunktowa oraz operator inwersji."""
        ch_edge = Chromosome(2, 8, (-5, 5), genes=[0] * 16)
        Mutation.edge_mutation(ch_edge, 1.0)
        self.assertEqual(sum(ch_edge.genes), 1)
        self.assertTrue(ch_edge.genes[0] == 1 or ch_edge.genes[-1] == 1)

        ch_one = Chromosome(2, 8, (-5, 5), genes=[0] * 16)
        Mutation.onepoint_mutation(ch_one, 1.0)
        self.assertEqual(sum(ch_one.genes), 1)

        ch_two = Chromosome(2, 8, (-5, 5), genes=[0] * 16)
        Mutation.twopoint_mutation(ch_two, 1.0)
        self.assertEqual(sum(ch_two.genes), 2)

        ch_inv = Chromosome(2, 8, (-5, 5), genes=list(range(16)))
        Mutation.inversion(ch_inv, 1.0)
        self.assertEqual(sorted(ch_inv.genes), list(range(16)))

    def test_elitism_and_min_max_and_exports(self):
        """Maksymalizacja/minimalizacja, elita liczbowo/%, historia, eksport CSV/JSON."""
        # Funkcja z maksimum w (0, 0) równym 10.0: f(x) = 10 - sum(x_i^2)
        ga = GeneticAlgorithm(
            pop_size=30,
            epochs=15,
            num_variables=3,
            bit_precision=12,
            bounds=(-5, 5),
            fitness_func=lambda x: 10.0 - sum(v * v for v in x),
            opt_type="max",
            elite_count=3,
        )
        history = ga.run(inv_prob=0.1, verbose=False)
        self.assertGreaterEqual(history[-1]["best_fitness"], history[0]["best_fitness"])
        self.assertGreater(ga.execution_time, 0.0)

        with tempfile.TemporaryDirectory() as tmp:
            csv_file = Path(tmp) / "out.csv"
            json_file = Path(tmp) / "out.json"
            ga.save_history_csv(csv_file)
            ga.save_history_json(json_file)
            self.assertTrue(csv_file.exists() and csv_file.stat().st_size > 0)
            self.assertTrue(json_file.exists() and json_file.stat().st_size > 0)

    def test_all_registered_functions(self):
        """Wszystkie funkcje w rejestrze (FunkcjeTestowe oraz CEC2014) dla różnych wymiarów."""
        for spec in FunctionRegistry.get_all():
            for dim in (5, 10, 27):
                fn = spec.create_evaluator(dim)
                val = fn([0.0] * dim)
                self.assertIsInstance(val, float)

    def test_real_chromosome_init_and_decode(self):
        """Inicjalizacja, klonowanie oraz dekodowanie chromosomu rzeczywistego."""
        ch = Chromosome(num_variables=5, bounds=(-5, 5))
        self.assertEqual(ch.representation, "real")
        self.assertIsNone(ch.bit_precision)
        self.assertEqual(ch.total_length, 5)
        self.assertEqual(len(ch.genes), 5)
        for val in ch.genes:
            self.assertGreaterEqual(val, -5.0)
            self.assertLessEqual(val, 5.0)

        decoded = ch.decode()
        self.assertEqual(decoded, ch.genes)
        decoded[0] = 999.0
        self.assertNotEqual(ch.genes[0], 999.0)

        cloned = ch.clone()
        self.assertEqual(cloned.representation, "real")
        self.assertEqual(cloned.genes, ch.genes)

    def test_real_crossover_operators(self):
        """Operatory krzyżowania rzeczywistego: uśredniające, arytmetyczne, linearne, BLX-alfa i BLX-alfa-beta."""
        p1 = Chromosome(2, "real", bounds=(-5, 5), genes=[2.0, -4.0])
        p2 = Chromosome(2, "real", bounds=(-5, 5), genes=[4.0, 2.0])

        # Uśredniające
        c1, c2 = Crossover.average_crossover(p1, p2, 1.0)
        self.assertEqual(c1.genes, [3.0, -1.0])
        self.assertEqual(c2.genes, [3.0, -1.0])

        # Arytmetyczne z zadanym współczynnikiem K
        c1, c2 = Crossover.arithmetic_crossover(p1, p2, 1.0, K=0.25)
        self.assertEqual(c1.genes, [3.5, 0.5])
        self.assertEqual(c2.genes, [2.5, -2.5])

        # Linearne (Wright 1991): 3 kandydatów Z, V, W -> wybór 2 najlepszych wg fitness_func
        lp1 = Chromosome(2, "real", bounds=(-5, 5), genes=[0.5, 0.5])
        lp2 = Chromosome(2, "real", bounds=(-5, 5), genes=[-0.5, -0.5])
        sphere = lambda x: sum(v * v for v in x)

        lc1, lc2 = Crossover.linear_crossover(lp1, lp2, 1.0, fitness_func=sphere, opt_type="min")
        # Z = [0.0, 0.0] (f=0.0), V = [1.0, 1.0] (f=2.0), W = [-1.0, -1.0] (f=2.0)
        self.assertEqual(lc1.genes, [0.0, 0.0])
        self.assertEqual(lc1.fitness, 0.0)
        self.assertIn(lc2.genes, ([1.0, 1.0], [-1.0, -1.0]))
        self.assertEqual(lc2.fitness, 2.0)

        lc_max1, lc_max2 = Crossover.linear_crossover(lp1, lp2, 1.0, fitness_func=sphere, opt_type="max")
        self.assertEqual(sorted([lc_max1.genes, lc_max2.genes]), [[-1.0, -1.0], [1.0, 1.0]])

        # BLX-alpha z niestandardowym alpha i zachowaniem granic
        random.seed(42)
        bc1, bc2 = Crossover.blx_alpha(p1, p2, 1.0, alpha=0.2)
        for idx, (lo, hi) in enumerate([(-5.0, 5.0), (-5.0, 5.0)]):
            d = abs(p1.genes[idx] - p2.genes[idx])
            exp_lo = max(lo, min(p1.genes[idx], p2.genes[idx]) - 0.2 * d)
            exp_hi = min(hi, max(p1.genes[idx], p2.genes[idx]) + 0.2 * d)
            self.assertGreaterEqual(bc1.genes[idx], exp_lo)
            self.assertLessEqual(bc1.genes[idx], exp_hi)
            self.assertGreaterEqual(bc2.genes[idx], exp_lo)
            self.assertLessEqual(bc2.genes[idx], exp_hi)

        # BLX-alpha-beta z asymetrycznym przedziałem (alpha=0.0, beta=1.0)
        abc1, abc2 = Crossover.blx_alpha_beta(p1, p2, 1.0, alpha=0.0, beta=1.0)
        for idx, (lo, hi) in enumerate([(-5.0, 5.0), (-5.0, 5.0)]):
            d = abs(p1.genes[idx] - p2.genes[idx])
            exp_lo = max(lo, min(p1.genes[idx], p2.genes[idx]))
            exp_hi = min(hi, max(p1.genes[idx], p2.genes[idx]) + 1.0 * d)
            self.assertGreaterEqual(abc1.genes[idx], exp_lo)
            self.assertLessEqual(abc1.genes[idx], exp_hi)
            self.assertGreaterEqual(abc2.genes[idx], exp_lo)
            self.assertLessEqual(abc2.genes[idx], exp_hi)

    def test_real_mutation_operators(self):
        """Mutacja równomierna oraz mutacja Gaussa z zadanym sigma i kontrolą granic."""
        ch_uni = Chromosome(3, "real", bounds=(-2, 2), genes=[10.0, 10.0, 10.0])
        ch_uni.fitness = 123.0
        Mutation.uniform_mutation(ch_uni, 1.0)
        self.assertIsNone(ch_uni.fitness)
        in_bounds = [g for g in ch_uni.genes if -2.0 <= g <= 2.0]
        self.assertEqual(len(in_bounds), 1)

        random.seed(123)
        ch_gauss = Chromosome(3, "real", bounds=(-1.0, 1.0), genes=[0.0, 0.0, 0.0])
        ch_gauss.fitness = 42.0
        Mutation.gaussian_mutation(ch_gauss, 1.0, sigma=0.05)
        self.assertIsNone(ch_gauss.fitness)
        changed = [g for g in ch_gauss.genes if g != 0.0]
        self.assertEqual(len(changed), 1)
        self.assertGreaterEqual(changed[0], -1.0)
        self.assertLessEqual(changed[0], 1.0)

    def test_real_genetic_algorithm_and_operator_validation(self):
        """Pełny przebieg AG dla reprezentacji rzeczywistej, eksport JSON oraz walidacja operatorów."""
        spec = FunctionRegistry.get_by_name("bf_hypersphere")
        evaluator = spec.create_evaluator(4)

        for cross_fn in (
            Crossover.average_crossover,
            Crossover.arithmetic_crossover,
            Crossover.linear_crossover,
            Crossover.blx_alpha,
            Crossover.blx_alpha_beta,
        ):
            for mut_fn in (Mutation.uniform_mutation, Mutation.gaussian_mutation):
                ga = GeneticAlgorithm(
                    pop_size=24,
                    epochs=8,
                    num_variables=4,
                    representation="real",
                    bounds=spec.default_bounds,
                    fitness_func=evaluator,
                    opt_type="min",
                    elite_percent=0.1,
                )
                history = ga.run(
                    crossover_method=cross_fn,
                    mutation_method=mut_fn,
                    cross_prob=0.8,
                    mut_prob=0.3,
                    alpha=0.4,
                    beta=0.2,
                    mutation_sigma=0.25,
                    verbose=False,
                )
                self.assertEqual(len(history), 8)
                self.assertGreater(ga.execution_time, 0.0)

        # Zapis JSON dla reprezentacji rzeczywistej
        with tempfile.TemporaryDirectory() as tmp:
            json_file = Path(tmp) / "real_out.json"
            ga.save_history_json(json_file)
            payload = json.loads(json_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["config"]["representation"], "real")
            self.assertIsNone(payload["config"]["bit_precision"])

        # Walidacja niezgodności operatorów
        ga_real = GeneticAlgorithm(10, 2, 3, representation="real", bounds=(-5, 5), fitness_func=evaluator)
        with self.assertRaises(ValueError):
            ga_real.run(crossover_method=Crossover.onepoint_crossover, verbose=False)
        with self.assertRaises(ValueError):
            ga_real.run(mutation_method=Mutation.onepoint_mutation, verbose=False)

        ga_bin = GeneticAlgorithm(10, 2, 3, representation="binary", bounds=(-5, 5), fitness_func=evaluator)
        with self.assertRaises(ValueError):
            ga_bin.run(crossover_method=Crossover.blx_alpha, verbose=False)
        with self.assertRaises(ValueError):
            ga_bin.run(mutation_method=Mutation.gaussian_mutation, verbose=False)


if __name__ == "__main__":
    unittest.main()

