import sys

from engine.algorithm import GeneticAlgorithm
from engine.crossover import Crossover
from engine.functions import FunctionRegistry
from engine.mutation import Mutation
from engine.selection import Selection


def run_cli_demo():
    """Pomocniczy tryb demonstracyjny (--cli) do szybkiego przetestowania silnika algorytmu."""
    spec = FunctionRegistry.get_by_name("bf_hypersphere")
    liczba_zmiennych = 5
    wielkosc_populacji = 50
    liczba_epok = 100
    dokladnosc_bitowa = 16

    print("--- INICJALIZACJA ALGORYTMU ---")
    ag = GeneticAlgorithm(
        pop_size=wielkosc_populacji,
        epochs=liczba_epok,
        num_variables=liczba_zmiennych,
        bit_precision=dokladnosc_bitowa,
        bounds=spec.default_bounds,
        fitness_func=spec.create_evaluator(liczba_zmiennych),
        opt_type="min",
        elite_percent=0.1,
    )

    print("\n--- START EWOLUCJI ---")
    ag.run(
        selection_method=Selection.tournament,
        crossover_method=Crossover.twopoint_crossover,
        mutation_method=Mutation.onepoint_mutation,
        cross_prob=0.8,
        mut_prob=0.05,
        inv_prob=0.05,
        selection_param=3,
    )

    najlepszy_koncowy = ag.best_individual or Selection.best(ag.population, 1, ag.opt_type)[0]
    wartosci_roz = [round(w, 5) for w in najlepszy_koncowy.decode()]

    print("\n--- WYNIK KOŃCOWY ---")
    print(f"Funkcja: {spec.name} (N={liczba_zmiennych})")
    print(f"Najlepsze znalezione argumenty: {wartosci_roz}")
    print(f"Wartość funkcji (Fitness): {najlepszy_koncowy.fitness:.6f}")
    print(f"Czas wykonania obliczeń: {ag.execution_time:.4f} s")

    csv_path = ag.save_history_csv("results/demo_run.csv")
    json_path = ag.save_history_json("results/demo_run.json")
    print(f"Zapisano wyniki kolejnych iteracji do: {csv_path} oraz {json_path}")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli_demo()
    else:
        from gui.app import launch_gui

        launch_gui()
