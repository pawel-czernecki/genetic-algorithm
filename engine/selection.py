import math
import random


class Selection:

    @staticmethod
    def _resolve_pool_size(pop_len, selection_param, min_size=2):
        """Pomocnicza metoda przeliczająca parametr selekcji (% lub liczbę osobników) na rozmiar puli."""
        if selection_param is None:
            return pop_len
        if isinstance(selection_param, float) and 0.0 < selection_param <= 1.0:
            size = math.ceil(pop_len * selection_param)
        else:
            size = int(selection_param)
        return max(min(min_size, pop_len), min(size, pop_len))

    # Selekcja najlepszych: wybiera pulę najlepszych osobników (wg parametru % lub liczby)
    # Gdy selection_param=None, zwraca dokładnie num_parents najlepszych osobników w kolejności.
    @staticmethod
    def best(population, num_parents, opt_type, selection_param=None):
        is_reverse = True if opt_type == "max" else False
        sorted_population = sorted(population, key=lambda x: x.fitness, reverse=is_reverse)

        if selection_param is None:
            return sorted_population[:num_parents]

        pool_size = Selection._resolve_pool_size(len(population), selection_param, min_size=max(2, num_parents))
        pool = sorted_population[:pool_size]
        if len(pool) >= num_parents:
            return random.sample(pool, num_parents)
        return [random.choice(pool) for _ in range(num_parents)]

    # Selekcja najgorszych: wybiera pulę najgorszych osobników (wg parametru % lub liczby)
    @staticmethod
    def worst(population, num_parents, opt_type, selection_param=None):
        is_reverse = True if opt_type == "min" else False
        sorted_population = sorted(population, key=lambda x: x.fitness, reverse=is_reverse)

        if selection_param is None:
            return sorted_population[:num_parents]

        pool_size = Selection._resolve_pool_size(len(population), selection_param, min_size=max(2, num_parents))
        pool = sorted_population[:pool_size]
        if len(pool) >= num_parents:
            return random.sample(pool, num_parents)
        return [random.choice(pool) for _ in range(num_parents)]

    # Selekcja turniejowa: zależnie od rozmiaru turnieju (tournament_size) losuje grupę i wybiera najlepszego
    @staticmethod
    def tournament(population, num_parents, opt_type, tournament_size=3):
        parents = []
        is_reverse = True if opt_type == "max" else False
        k = max(1, min(int(tournament_size) if tournament_size is not None else 3, len(population)))

        for _ in range(num_parents):
            contenders = random.sample(population, k)
            contenders.sort(key=lambda x: x.fitness, reverse=is_reverse)
            parents.append(contenders[0])

        return parents

    # Selekcja kołem ruletki: prawdopodobieństwo wyboru proporcjonalne do dopasowania (fitness)
    @staticmethod
    def roulette(population, num_parents, opt_type, selection_param=None):
        fitness_values = [ind.fitness for ind in population]

        # Eliminacja liczb ujemnych i przeskalowanie dla min/max
        if opt_type == "max":
            min_fit = min(fitness_values)
            adjusted_fitness = [f - min_fit + 1e-6 for f in fitness_values]
        else:
            max_fit = max(fitness_values)
            adjusted_fitness = [max_fit - f + 1e-6 for f in fitness_values]

        total_fitness = sum(adjusted_fitness)
        if total_fitness <= 0 or math.isnan(total_fitness) or math.isinf(total_fitness):
            return [random.choice(population) for _ in range(num_parents)]

        probabilities = [f / total_fitness for f in adjusted_fitness]
        return random.choices(population, weights=probabilities, k=num_parents)
