import os
from pathlib import Path
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
        """Pkt 2 i 4a: Dowolna liczba zmiennych (5, 10, 20, 27) oraz dokładność bitowa i dziesiętna."""
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
        ch = Chromosome(num_variables=5, bounds=(-10, 10), decimal_precision=4)
        self.assertEqual(ch.bit_precision, 18)  # ceil(log2(20 * 10^4 + 1)) = 18

    def test_selection_methods(self):
        """Pkt 4d: Selekcja najlepszych, najgorszych, ruletki i turniejowa + parametry."""
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
        """Pkt 4e: Krzyżowanie jednopunktowe, dwupunktowe, jednorodne, ziarniste."""
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
        """Pkt 4f i 4g: Mutacja brzegowa, jedno- i dwupunktowa oraz operator inwersji."""
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
        """Pkt 2, 4h, 8, 9, 10: Maksymalizacja/minimalizacja, elita liczbowo/%, historia, eksport CSV/JSON."""
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
        """Pkt 5: Wszystkie funkcje w rejestrze (FunkcjeTestowe oraz CEC2014) dla różnych wymiarów."""
        for spec in FunctionRegistry.get_all():
            for dim in (5, 10, 27):
                fn = spec.create_evaluator(dim)
                val = fn([0.0] * dim)
                self.assertIsInstance(val, float)


if __name__ == "__main__":
    unittest.main()

