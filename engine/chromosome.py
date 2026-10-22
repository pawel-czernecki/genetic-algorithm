import math
import random


class Chromosome:
    def __init__(self, num_variables, bit_precision=16, bounds=None, genes=None, decimal_precision=None):
        """
        Inicjalizacja pojedynczego osobnika (chromosomu) w reprezentacji binarnej.
        :param num_variables: Liczba zmiennych funkcji celu (np. 2, 5, 10, 20, 27).
        :param bit_precision: Liczba bitów przypadająca na jedną zmienną (dokładność bitowa).
        :param bounds: Przedział (min, max) lub lista przedziałów [(min_1, max_1), ...] dla zmiennych.
        :param genes: Opcjonalna lista bitów (0/1); jeśli None, geny są losowane.
        :param decimal_precision: Opcjonalna dokładność dziesiętna d (10^-d); jeśli podana,
                                  wylicza liczbę bitów ze wzoru: ceil(log2((b - a) * 10^d + 1)).
        """
        if num_variables < 1:
            raise ValueError("Liczba zmiennych (num_variables) musi być >= 1.")

        self.num_variables = int(num_variables)
        self.bounds = self._normalize_bounds(bounds, self.num_variables)
        self.decimal_precision = decimal_precision

        if decimal_precision is not None:
            min_val, max_val = self.bounds[0]
            span = max(abs(max_val - min_val), 1e-12)
            computed_bits = math.ceil(math.log2(span * (10 ** decimal_precision) + 1))
            self.bit_precision = max(2, int(computed_bits))
        else:
            self.bit_precision = max(2, int(bit_precision))

        # Całkowita długość chromosomu
        self.total_length = self.num_variables * self.bit_precision

        # Inicjalizacja genomu
        if genes is not None:
            self.genes = list(genes)
        else:
            self.genes = [random.randint(0, 1) for _ in range(self.total_length)]

        # Ocena (fitness)
        self.fitness = None

    @staticmethod
    def _normalize_bounds(bounds, num_variables):
        if bounds is None:
            return [(-10.0, 10.0)] * num_variables
        # Jeśli przekazano pojedynczą krotkę np. (-10, 10)
        if (
            isinstance(bounds, (tuple, list))
            and len(bounds) == 2
            and isinstance(bounds[0], (int, float))
            and isinstance(bounds[1], (int, float))
        ):
            return [(float(bounds[0]), float(bounds[1]))] * num_variables
        # Jeśli przekazano listę przedziałów
        normalized = [(float(b[0]), float(b[1])) for b in bounds]
        if len(normalized) == 1 and num_variables > 1:
            return normalized * num_variables
        if len(normalized) < num_variables:
            last = normalized[-1]
            normalized.extend([last] * (num_variables - len(normalized)))
        return normalized[:num_variables]

    def clone(self):
        """Szybkie klonowanie osobnika bez kosztownego kopiowania definicji granic."""
        copied = Chromosome.__new__(Chromosome)
        copied.num_variables = self.num_variables
        copied.bit_precision = self.bit_precision
        copied.bounds = self.bounds
        copied.decimal_precision = self.decimal_precision
        copied.total_length = self.total_length
        copied.genes = self.genes.copy()
        copied.fitness = self.fitness
        return copied

    def __deepcopy__(self, memo):
        return self.clone()

    def decode(self):
        """Rozkodowanie binarnego chromosomu na wektor wartości rzeczywistych."""
        decoded_values = []
        denom = (1 << self.bit_precision) - 1

        for i in range(self.num_variables):
            start_index = i * self.bit_precision
            end_index = start_index + self.bit_precision

            # Zamiana ciągu bitów na liczbę dziesiętną
            decimal_value = 0
            for bit in self.genes[start_index:end_index]:
                decimal_value = (decimal_value << 1) | bit

            min_val, max_val = self.bounds[i]
            # Wartość rzeczywista ze wzoru: a + dec * (b - a) / (2^m - 1)
            real_value = min_val + decimal_value * (max_val - min_val) / denom
            decoded_values.append(real_value)

        return decoded_values
