import copy
import random


class Crossover:

    # Prawdopodobieństwo krzyżowania
    @staticmethod
    def should_be_crossovered(prob):
        return random.random() <= prob

    @staticmethod
    def _clamp(val, min_val, max_val):
        """Pilnuje, aby wartość genu nie wyszła poza dopuszczalny przedział [min_val, max_val]."""
        return max(min_val, min(max_val, val))

    # Krzyżowanie uśredniające (reprezentacja rzeczywista)
    @staticmethod
    def average_crossover(parent1, parent2, prob):
        child1 = copy.deepcopy(parent1)
        child2 = copy.deepcopy(parent2)

        if Crossover.should_be_crossovered(prob):
            for i in range(parent1.num_variables):
                min_bound, max_bound = parent1.bounds[i]
                avg_val = Crossover._clamp((parent1.genes[i] + parent2.genes[i]) / 2.0, min_bound, max_bound)
                child1.genes[i] = avg_val
                child2.genes[i] = avg_val

            child1.fitness, child2.fitness = None, None

        return child1, child2

    # Krzyżowanie arytmetyczne (reprezentacja rzeczywista)
    @staticmethod
    def arithmetic_crossover(parent1, parent2, prob, K=None):
        child1 = copy.deepcopy(parent1)
        child2 = copy.deepcopy(parent2)

        if Crossover.should_be_crossovered(prob):
            k_val = random.random() if K is None else K

            for i in range(parent1.num_variables):
                min_bound, max_bound = parent1.bounds[i]
                val1 = k_val * parent1.genes[i] + (1.0 - k_val) * parent2.genes[i]
                val2 = (1.0 - k_val) * parent1.genes[i] + k_val * parent2.genes[i]
                child1.genes[i] = Crossover._clamp(val1, min_bound, max_bound)
                child2.genes[i] = Crossover._clamp(val2, min_bound, max_bound)

            child1.fitness, child2.fitness = None, None

        return child1, child2

    # Krzyżowanie linearne (Wright, 1991) – 3 kandydatów (Z, V, W) i wybór 2 najlepszych wg funkcji celu
    @staticmethod
    def linear_crossover(parent1, parent2, prob, fitness_func=None, opt_type="min"):
        if not Crossover.should_be_crossovered(prob):
            return copy.deepcopy(parent1), copy.deepcopy(parent2)

        cand_z = copy.deepcopy(parent1)
        cand_v = copy.deepcopy(parent1)
        cand_w = copy.deepcopy(parent1)
        cand_z.fitness = None
        cand_v.fitness = None
        cand_w.fitness = None

        for i in range(parent1.num_variables):
            g1, g2 = parent1.genes[i], parent2.genes[i]
            min_bound, max_bound = parent1.bounds[i]
            cand_z.genes[i] = Crossover._clamp(0.5 * g1 + 0.5 * g2, min_bound, max_bound)
            cand_v.genes[i] = Crossover._clamp(1.5 * g1 - 0.5 * g2, min_bound, max_bound)
            cand_w.genes[i] = Crossover._clamp(-0.5 * g1 + 1.5 * g2, min_bound, max_bound)

        if fitness_func is not None:
            for cand in (cand_z, cand_v, cand_w):
                cand.fitness = float(fitness_func(cand.decode()))
            best_three = sorted(
                (cand_z, cand_v, cand_w),
                key=lambda c: c.fitness,
                reverse=(opt_type == "max"),
            )
            return best_three[0], best_three[1]

        return cand_v, cand_w

    # Krzyżowanie mieszające typu alfa (BLX-alpha)
    @staticmethod
    def blx_alpha(parent1, parent2, prob, alpha=0.5):
        return Crossover.blx_alpha_beta(parent1, parent2, prob, alpha=alpha, beta=alpha)

    # Krzyżowanie mieszające typu alfa i beta (BLX-alpha-beta)
    @staticmethod
    def blx_alpha_beta(parent1, parent2, prob, alpha=0.5, beta=0.25):
        child1 = copy.deepcopy(parent1)
        child2 = copy.deepcopy(parent2)

        if Crossover.should_be_crossovered(prob):
            for i in range(parent1.num_variables):
                v1, v2 = parent1.genes[i], parent2.genes[i]
                d = abs(v1 - v2)
                min_v = min(v1, v2) - alpha * d
                max_v = max(v1, v2) + beta * d

                min_bound, max_bound = parent1.bounds[i]
                child1.genes[i] = Crossover._clamp(random.uniform(min_v, max_v), min_bound, max_bound)
                child2.genes[i] = Crossover._clamp(random.uniform(min_v, max_v), min_bound, max_bound)

            child1.fitness, child2.fitness = None, None

        return child1, child2

    # Krzyżowanie jednopunktowe
    @staticmethod
    def onepoint_crossover(parent1, parent2, prob):
        child1 = copy.deepcopy(parent1)
        child2 = copy.deepcopy(parent2)

        if Crossover.should_be_crossovered(prob) and parent1.total_length >= 2:
            point = random.randint(1, parent1.total_length - 1)
            child1.genes[point:] = parent2.genes[point:]
            child2.genes[point:] = parent1.genes[point:]

            child1.fitness, child2.fitness = None, None

        return child1, child2

    # Krzyżowanie dwupunktowe (wymiana bitów pomiędzy 2 losowymi punktami)
    @staticmethod
    def twopoint_crossover(parent1, parent2, prob):
        child1 = copy.deepcopy(parent1)
        child2 = copy.deepcopy(parent2)

        if Crossover.should_be_crossovered(prob):
            if parent1.total_length >= 3:
                point1, point2 = sorted(random.sample(range(1, parent1.total_length), 2))
            else:
                point1, point2 = 0, max(1, parent1.total_length - 1)

            child1.genes[point1:point2] = parent2.genes[point1:point2]
            child2.genes[point1:point2] = parent1.genes[point1:point2]

            child1.fitness, child2.fitness = None, None

        return child1, child2

    # Krzyżowanie jednorodne (50/50 szans na wymianę każdego bitu pomiędzy rodzicami)
    @staticmethod
    def uniform_crossover(parent1, parent2, prob):
        child1 = copy.deepcopy(parent1)
        child2 = copy.deepcopy(parent2)

        if Crossover.should_be_crossovered(prob):
            for i in range(parent1.total_length):
                if random.random() < 0.5:
                    child1.genes[i], child2.genes[i] = child2.genes[i], child1.genes[i]

            child1.fitness, child2.fitness = None, None

        return child1, child2

    # Krzyżowanie ziarniste (losowa maska binarna / wymiana bloków genów)
    @staticmethod
    def granular(parent1, parent2, prob, grain_size=None):
        child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)

        if Crossover.should_be_crossovered(prob):
            # Jeśli nie podano rozmiaru ziarna, używamy bloków odpowiadających zmiennym
            # (lub pojedynczych bitów wg maski, gdy zmienna jest tylko 1)
            block_len = grain_size if grain_size is not None else (
                parent1.bit_precision if parent1.num_variables > 1 else max(1, parent1.bit_precision // 4)
            )
            block_len = max(1, int(block_len))

            for start in range(0, parent1.total_length, block_len):
                if random.random() <= 0.5:
                    end = min(start + block_len, parent1.total_length)
                    child1.genes[start:end], child2.genes[start:end] = (
                        child2.genes[start:end],
                        child1.genes[start:end],
                    )

            child1.fitness, child2.fitness = None, None

        return child1, child2
