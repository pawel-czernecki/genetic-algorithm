import copy
import random


class Crossover:

    # Prawdopodobieństwo krzyżowania
    @staticmethod
    def should_be_crossovered(prob):
        return random.random() <= prob

    @staticmethod
    def _clamp(val, min_val, max_val):
        """Pomocnicza funkcja pilnująca, by wyliczony gen nie wyszedł poza granice dziedziny."""
        return max(min_val, min(max_val, val))
    
    #Krzyżowanie uśredniające
    @staticmethod
    def average_crossover(parent1, parent2, prob):
        child1 = copy.deepcopy(parent1)
        child2 = copy.deepcopy(parent2)

        if Crossover.should_be_crossovered(prob):
            for i in range(parent1.num_variables):
                child1.genes[i] = (parent1.genes[i] + parent2.genes[i]) / 2.0
                child2.genes[i] = (parent1.genes[i] + parent2.genes[i]) / 2.0

        child1.fitness, child2.fitness = None, None
        return child1, child2

    #Krzyżowanie arytmetyczne
    @staticmethod
    def arithmetic_crossover(parent1, parent2, prob, K=None):
        child1 = copy.deepcopy(parent1)
        child2 = copy.deepcopy(parent2)

        if Crossover.should_be_crossovered(prob):
            if K is None:
                k_val = random.random()
            else:
                k_val = K

            for i in range(parent1.num_variables):
                child1.genes[i] = k_val * parent1.genes[i] + (1 - k_val) * parent2.genes[i]
                child2.genes[i] = (1 - k_val) * parent1.genes[i] + k_val * parent2.genes[i]

        child1.fitness, child2.fitness = None, None
        return child1, child2
    
    #Krzyżowanie liniowe
    @staticmethod
    def linear_crossover(parent1, parent2, prob):
        child1 = copy.deepcopy(parent1)
        child2 = copy.deepcopy(parent2) 

        if Crossover.should_be_crossovered(prob):
            for i in range(parent1.num_variables):
                # Generujemy dwa wektory eksploracyjne
                val1 = (1.5 * parent1.genes[i]) - (0.5 * parent2.genes[i])
                val2 = (-0.5 * parent1.genes[i]) + (1.5 * parent2.genes[i])
                
                # Zabezpieczamy wartości przed wypadnięciem poza granice funkcji
                min_bound, max_bound = parent1.bounds[i]
                child1.genes[i] = Crossover._clamp(val1, min_bound, max_bound)
                child2.genes[i] = Crossover._clamp(val2, min_bound, max_bound)

        child1.fitness, child2.fitness = None, None
        return child1, child2

    #Krzyżowanie mieszające typu alfa 
    @staticmethod
    def blx_alpha(parent1, parent2, prob, alpha=0.5):
        child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)
        if Crossover.should_be_crossovered(prob):
            for i in range(parent1.num_variables):
                v1, v2 = parent1.genes[i], parent2.genes[i]
                d = abs(v1 - v2)
                
                # Tworzymy rozszerzony przedział i losujemy z niego wartości
                min_v = min(v1, v2) - alpha * d
                max_v = max(v1, v2) + alpha * d
                
                min_bound, max_bound = parent1.bounds[i]
                child1.genes[i] = Crossover._clamp(random.uniform(min_v, max_v), min_bound, max_bound)
                child2.genes[i] = Crossover._clamp(random.uniform(min_v, max_v), min_bound, max_bound)
            child1.fitness, child2.fitness = None, None
        return child1, child2

    #Krzyżowanie mieszające typu alfa i beta (BLX-alpha-beta)
    @staticmethod
    def blx_alpha_beta(parent1, parent2, prob, alpha=0.5, beta=0.25):
        child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)
        if Crossover.should_be_crossovered(prob):
            for i in range(parent1.num_variables):
                v1, v2 = parent1.genes[i], parent2.genes[i]
                d = abs(v1 - v2)
                
                # Asymetryczne rozszerzenie przedziału - inne dla minimum, inne dla maksimum
                min_v = min(v1, v2) - alpha * d
                max_v = max(v1, v2) + beta * d
                
                min_bound, max_bound = parent1.bounds[i]
                child1.genes[i] = Crossover._clamp(random.uniform(min_v, max_v), min_bound, max_bound)
                child2.genes[i] = Crossover._clamp(random.uniform(min_v, max_v), min_bound, max_bound)
            child1.fitness, child2.fitness = None, None
        return child1, child2

    #Krzyżowanie jednopunktowe
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

    #Krzyżowanie dwupunktowe (wymiana bitów pomiędzy 2 losowymi punktami)
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

    #Krzyżowanie jednorodne (50/50 szans na wymianę każdego bitu pomiędzy rodzicami)
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

    #Krzyżowanie ziarniste (losowa maska binarna / wymiana bloków genów)
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


  
