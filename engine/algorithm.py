import csv
import json
import math
import statistics
import time
from pathlib import Path

from engine.chromosome import Chromosome
from engine.crossover import Crossover
from engine.mutation import Mutation
from engine.selection import Selection


class GeneticAlgorithm:
    def __init__(
        self,
        pop_size,
        epochs,
        num_variables,
        bit_precision=16,
        bounds=None,
        fitness_func=None,
        opt_type="min",
        elite_percent=0.1,
        elite_count=None,
        decimal_precision=None,
    ):
        self.pop_size = int(pop_size)
        self.epochs = int(epochs)
        self.fitness_func = fitness_func
        self.opt_type = opt_type
        self.elite_percent = elite_percent
        self.elite_count = elite_count
        self.num_variables = int(num_variables)
        self.bit_precision = int(bit_precision) if bit_precision is not None else 16
        self.decimal_precision = decimal_precision
        self.bounds = Chromosome._normalize_bounds(bounds, self.num_variables)

        self.population = []
        self.history = []
        self.execution_time = 0.0
        self.best_individual = None
        self._initialize_population()

    def _initialize_population(self):
        self.population = [
            Chromosome(
                num_variables=self.num_variables,
                bit_precision=self.bit_precision,
                bounds=self.bounds,
                decimal_precision=self.decimal_precision,
            )
            for _ in range(self.pop_size)
        ]
        if self.population:
            self.bit_precision = self.population[0].bit_precision

    def _get_elite_count(self):
        if self.elite_count is not None:
            return max(0, min(int(self.elite_count), self.pop_size))
        if self.elite_percent is None or self.elite_percent <= 0:
            return 0
        pct = self.elite_percent / 100.0 if self.elite_percent > 1.0 else float(self.elite_percent)
        return max(0, min(math.ceil(self.pop_size * pct), self.pop_size))

    def evaluate_population(self):
        for osobnik in self.population:
            if osobnik.fitness is None:
                decoded_values = osobnik.decode()
                osobnik.fitness = float(self.fitness_func(decoded_values))

    def _select_parents(self, selection_method, selection_param):
        if selection_method in (Selection.best, Selection.worst):
            param = 0.5 if selection_param is None else selection_param
            return selection_method(self.population, 2, self.opt_type, param)
        elif selection_method == Selection.tournament:
            param = 3 if selection_param is None else int(selection_param)
            return selection_method(self.population, 2, self.opt_type, param)
        else:
            try:
                return selection_method(self.population, 2, self.opt_type, selection_param)
            except TypeError:
                return selection_method(self.population, 2, self.opt_type)

    def _record_epoch_stats(self, epoch_idx, start_time):
        fitness_values = [ind.fitness for ind in self.population]
        best_ind = Selection.best(self.population, 1, self.opt_type)[0]
        worst_ind = Selection.worst(self.population, 1, self.opt_type)[0]
        mean_fit = statistics.fmean(fitness_values)
        std_fit = statistics.pstdev(fitness_values) if len(fitness_values) > 1 else 0.0

        if self.best_individual is None:
            self.best_individual = best_ind.clone()
        else:
            if (self.opt_type == "min" and best_ind.fitness < self.best_individual.fitness) or (
                self.opt_type == "max" and best_ind.fitness > self.best_individual.fitness
            ):
                self.best_individual = best_ind.clone()

        stats = {
            "epoch": epoch_idx,
            "best_fitness": best_ind.fitness,
            "global_best_fitness": self.best_individual.fitness,
            "worst_fitness": worst_ind.fitness,
            "mean_fitness": mean_fit,
            "std_fitness": std_fit,
            "best_variables": best_ind.decode(),
            "elapsed_time_sec": time.perf_counter() - start_time,
        }
        self.history.append(stats)
        return best_ind, stats

    def run(
        self,
        selection_method=Selection.tournament,
        crossover_method=Crossover.onepoint_crossover,
        mutation_method=Mutation.onepoint_mutation,
        cross_prob=0.8,
        mut_prob=0.3,
        inv_prob=0.3,
        selection_param=None,
        progress_callback=None,
        verbose=True,
    ):
        """Główna pętla ewolucyjna."""
        self.history = []
        self.best_individual = None
        start_time = time.perf_counter()

        # Wstępna ocena populacji początkowej
        self.evaluate_population()
        elite_num = self._get_elite_count()

        for epoch in range(self.epochs):
            new_population = []

            # Strategia elitarna (% lub liczba osobników najlepszych)
            if elite_num > 0:
                elity = Selection.best(self.population, elite_num, self.opt_type)
                new_population.extend(ind.clone() for ind in elity)

            # Tworzenie nowej populacji: selekcja, krzyżowanie, mutacja, inwersja
            while len(new_population) < self.pop_size:
                rodzice = self._select_parents(selection_method, selection_param)

                # Krzyżowanie z prawdopodobieństwem cross_prob
                dziecko1, dziecko2 = crossover_method(rodzice[0], rodzice[1], cross_prob)

                # Mutacja z prawdopodobieństwem mut_prob
                if mutation_method is not None and mut_prob > 0:
                    mutation_method(dziecko1, mut_prob)
                    mutation_method(dziecko2, mut_prob)

                # Inwersja z prawdopodobieństwem inv_prob
                if inv_prob > 0:
                    Mutation.inversion(dziecko1, inv_prob)
                    Mutation.inversion(dziecko2, inv_prob)

                new_population.append(dziecko1)
                if len(new_population) < self.pop_size:
                    new_population.append(dziecko2)

            # Zastąpienie starej populacji nową i ocena osobników
            self.population = new_population
            self.evaluate_population()

            najlepszy, stats = self._record_epoch_stats(epoch + 1, start_time)
            if verbose:
                print(
                    f"Epoka {epoch + 1}/{self.epochs} | "
                    f"Najlepszy: {najlepszy.fitness:.6f} | "
                    f"Średnia: {stats['mean_fitness']:.6f} | "
                    f"Std: {stats['std_fitness']:.6f}"
                )
            if progress_callback is not None:
                progress_callback(epoch + 1, self.epochs, stats)

        self.execution_time = time.perf_counter() - start_time
        return self.history

    def save_history_csv(self, filepath, metadata=None):
        """Zapisuje historię przebiegu algorytmu z kolejnych iteracji do pliku CSV."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "epoch",
            "best_fitness",
            "global_best_fitness",
            "mean_fitness",
            "std_fitness",
            "worst_fitness",
            "elapsed_time_sec",
            "best_variables",
        ]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.history:
                writer.writerow(
                    {
                        "epoch": row["epoch"],
                        "best_fitness": f"{row['best_fitness']:.8f}",
                        "global_best_fitness": f"{row['global_best_fitness']:.8f}",
                        "mean_fitness": f"{row['mean_fitness']:.8f}",
                        "std_fitness": f"{row['std_fitness']:.8f}",
                        "worst_fitness": f"{row['worst_fitness']:.8f}",
                        "elapsed_time_sec": f"{row['elapsed_time_sec']:.6f}",
                        "best_variables": json.dumps([round(v, 6) for v in row["best_variables"]]),
                    }
                )
        return str(path)

    def save_history_json(self, filepath, metadata=None):
        """Zapisuje historię przebiegu algorytmu oraz podsumowanie konfiguracji do pliku JSON."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        best_final = self.best_individual or Selection.best(self.population, 1, self.opt_type)[0]
        payload = {
            "metadata": metadata or {},
            "config": {
                "pop_size": self.pop_size,
                "epochs": self.epochs,
                "num_variables": self.num_variables,
                "bit_precision": self.bit_precision,
                "decimal_precision": self.decimal_precision,
                "bounds": self.bounds,
                "opt_type": self.opt_type,
                "elite_count": self._get_elite_count(),
            },
            "summary": {
                "execution_time_sec": round(self.execution_time, 6),
                "best_fitness": best_final.fitness,
                "best_variables": best_final.decode(),
            },
            "iterations": self.history,
        }
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return str(path)
