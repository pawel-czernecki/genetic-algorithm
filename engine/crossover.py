import copy
import random


class Crossover:

    # Prawdopodobieństwo krzyżowania
    @staticmethod
    def should_be_crossovered(prob):
        return random.random() <= prob

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
