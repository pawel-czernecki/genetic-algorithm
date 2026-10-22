import random


class Mutation:

    # Prawdopodobieństwo mutacji
    @staticmethod
    def should_be_mutated(prob):
        return random.random() <= prob

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
