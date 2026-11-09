import random


class Mutation:

    # Prawdopodobieństwo mutacji
    @staticmethod
    def should_be_mutated(prob):
        return random.random() <= prob

    #Mutacja równomierna
    @staticmethod
    def uniform_mutation(chromosome, prob):
        if Mutation.should_be_mutated(prob):
            indeks = random.randint(0, chromosome.total_length - 1)

            min_b, max_b = chromosome.bounds[indeks]

            chromosome.genes[indeks] = random.uniform(min_b, max_b)

            chromosome.fitness = None

    #Mutacja Gaussa
    @staticmethod
    def gaussian_mutation(chromosome, prob, sigma=None):
        if Mutation.should_be_mutated(prob):
            indeks = random.randint(0, chromosome.total_length - 1)

            old_value = chromosome.genes[indeks]
            min_b, max_b = chromosome.bounds[indeks]

            if sigma is None:
                sigma = (max_b - min_b) * 0.1

            szum = random.gauss(0.0, sigma)
            new_value = old_value + szum

            new_value = max(min_b, min(max_b, new_value))

            chromosome.genes[indeks] = new_value
            chromosome.fitness = None


    # Prawdopodobieństwo inwersji
    @staticmethod
    def should_use_inversion(prob):
        return random.random() <= prob

    # Mutacja brzegowa (1 bit z końca lub z początku chromosomu, 50/50)
    @staticmethod
    def edge_mutation(chromosome, prob):
        if Mutation.should_be_mutated(prob):
            if random.random() < 0.5:
                chromosome.genes[chromosome.total_length - 1] = 1 - chromosome.genes[chromosome.total_length - 1]
            else:
                chromosome.genes[0] = 1 - chromosome.genes[0]

            # Zerujemy ocenę tylko wtedy, gdy zaszła mutacja
            chromosome.fitness = None

    # Mutacja jednopunktowa (odwrócenie 1 losowego bitu)
    @staticmethod
    def onepoint_mutation(chromosome, prob):
        if Mutation.should_be_mutated(prob):
            point = random.randint(0, chromosome.total_length - 1)
            chromosome.genes[point] = 1 - chromosome.genes[point]

            chromosome.fitness = None

    # Mutacja dwupunktowa (odwrócenie 2 różnych losowych bitów)
    @staticmethod
    def twopoint_mutation(chromosome, prob):
        if Mutation.should_be_mutated(prob):
            if chromosome.total_length >= 2:
                point1, point2 = random.sample(range(chromosome.total_length), 2)
                chromosome.genes[point1] = 1 - chromosome.genes[point1]
                chromosome.genes[point2] = 1 - chromosome.genes[point2]
            else:
                chromosome.genes[0] = 1 - chromosome.genes[0]

            chromosome.fitness = None

    # Operator inwersji (odwrócenie kolejności bitów pomiędzy 2 losowymi punktami)
    @staticmethod
    def inversion(chromosome, prob):
        if Mutation.should_use_inversion(prob) and chromosome.total_length >= 2:
            point1, point2 = sorted(random.sample(range(chromosome.total_length), 2))
            chromosome.genes[point1 : point2 + 1] = chromosome.genes[point1 : point2 + 1][::-1]
            chromosome.fitness = None