import math
import random


_UNSET = object()


class Chromosome:
    def __init__(
        self,
        num_variables,
        representation="real",
        bit_precision=_UNSET,
        bounds=_UNSET,
        genes=_UNSET,
        decimal_precision=_UNSET,
    ):
        """
        Inicjalizacja pojedynczego osobnika (chromosomu) w reprezentacji rzeczywistej lub binarnej.
        :param num_variables: Liczba zmiennych funkcji celu (np. 2, 5, 10, 20, 27).
        :param representation: Typ reprezentacji ('real' lub 'binary'). Ze względów kompatybilności
                               wstecznej przekazanie int jako 2. argumentu pozycyjnego traktowane jest
                               jako wywołanie binarne z podanym bit_precision.
        :param bit_precision: Liczba bitów przypadająca na jedną zmienną (tylko dla reprezentacji binarnej).
        :param bounds: Przedział (min, max) lub lista przedziałów [(min_1, max_1), ...] dla zmiennych.
        :param genes: Opcjonalna lista genów (wartości float dla 'real' lub bitów 0/1 dla 'binary').
        :param decimal_precision: Opcjonalna dokładność dziesiętna d (10^-d) dla reprezentacji binarnej;
                                  wylicza liczbę bitów ze wzoru: ceil(log2((b - a) * 10^d + 1)).
        """
        if num_variables < 1:
            raise ValueError("Liczba zmiennych (num_variables) musi być >= 1.")

        # Kompatybilność wsteczna z wywołaniami pozycyjnymi z Projektu 1:
        # Chromosome(num_variables, bit_precision, bounds, genes, decimal_precision)
        if isinstance(representation, int) and not isinstance(representation, bool):
            actual_bit_precision = representation
            actual_bounds = None if bit_precision is _UNSET else bit_precision
            actual_genes = (
                (None if bounds is _UNSET else bounds)
                if genes is _UNSET
                else genes
            )
            actual_decimal_precision = (
                (None if genes is _UNSET or bounds is _UNSET else genes)
                if decimal_precision is _UNSET
                else decimal_precision
            )
            if decimal_precision is _UNSET and bounds is not _UNSET and genes is not _UNSET and isinstance(genes, int):
                actual_genes = bounds
                actual_decimal_precision = genes
            representation = "binary"
            bit_precision = actual_bit_precision
            bounds = actual_bounds
            genes = actual_genes
            decimal_precision = actual_decimal_precision
        else:
            if bit_precision is _UNSET:
                bit_precision = 16
            if bounds is _UNSET:
                bounds = None
            if genes is _UNSET:
                genes = None
            if decimal_precision is _UNSET:
                decimal_precision = None

        if representation not in ("real", "binary"):
            raise ValueError(f"Nieobsługiwana reprezentacja chromosomu: {representation!r}. Dozwolone: 'real', 'binary'.")

        self.num_variables = int(num_variables)
        self.representation = representation
        self.bounds = self._normalize_bounds(bounds, self.num_variables)
        self.decimal_precision = decimal_precision
        self.fitness = None

        if self.representation == "binary":
            if decimal_precision is not None:
                min_val, max_val = self.bounds[0]
                span = max(abs(max_val - min_val), 1e-12)
                computed_bits = math.ceil(math.log2(span * (10 ** decimal_precision) + 1))
                self.bit_precision = max(2, int(computed_bits))
            else:
                self.bit_precision = max(2, int(bit_precision))

            # Całkowita długość chromosomu binarnego
            self.total_length = self.num_variables * self.bit_precision

            if genes is not None:
                self.genes = list(genes)
            else:
                self.genes = [random.randint(0, 1) for _ in range(self.total_length)]
        else:
            # Reprezentacja rzeczywista: jeden gen = jedna zmienna decyzyjna
            self.bit_precision = None
            self.total_length = self.num_variables

            if genes is not None:
                self.genes = list(genes)
            else:
                self.genes = [
                    random.uniform(self.bounds[i][0], self.bounds[i][1])
                    for i in range(self.num_variables)
                ]

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
        copied.representation = self.representation
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
        """Rozkodowanie chromosomu na wektor wartości rzeczywistych."""
        if self.representation == "real":
            return list(self.genes)

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
