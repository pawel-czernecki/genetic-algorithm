# Projekt 1 – Implementacja klasycznego algorytmu genetycznego

Projekt realizowany w ramach przedmiotu **Obliczenia Ewolucyjne**. Aplikacja implementuje klasyczny algorytm genetyczny z binarną reprezentacją chromosomu do optymalizacji (minimalizacji oraz maksymalizacji) funkcji wielu zmiennych wraz z interfejsem graficznym (GUI) w technologii `Tkinter / ttk` + `Matplotlib`.

## Struktura projektu

- `main.py` – punkt wejścia aplikacji (domyślnie uruchamia GUI; z flagą `--cli` uruchamia testowy przebieg w konsoli)
- `engine/`
  - `chromosome.py` – klasa `Chromosome` (reprezentacja binarna, dekodowanie przedziałowe, konfiguracja dokładności bitowej lub dziesiętnej $10^{-d}$)
  - `selection.py` – klasa `Selection` (selekcja najlepszych, najgorszych, kołem ruletki, turniejowa wraz z parametrami)
  - `crossover.py` – klasa `Crossover` (krzyżowanie jednopunktowe, dwupunktowe, jednorodne, ziarniste)
  - `mutation.py` – klasa `Mutation` (mutacja brzegowa, jednopunktowa, dwupunktowa oraz operator inwersji)
  - `algorithm.py` – klasa `GeneticAlgorithm` (główna pętla ewolucyjna, elitaryzm % lub liczbowy, pomiar czasu, statystyki epok, zapis do CSV i JSON)
  - `functions.py` – klasy `BenchmarkFunctionSpec` oraz `FunctionRegistry` wykorzystujące funkcje z bibliotek `benchmark_functions` oraz `opfunu` (`CEC2014`)
- `gui/`
  - `app.py` – klasa `GeneticAlgorithmGUI` (interfejs graficzny, pełna konfiguracja parametrów, wykresy 9a i 9b, tabela iteracji, tryb 10 uruchomień do sprawozdania, eksport CSV/JSON/PNG)
- `tests/`
  - `test_algorithm.py` – testy jednostkowe weryfikujące wszystkie komponenty algorytmu

## Wymagania środowiska i instalacja

Zalecany Python `>= 3.10`. Wymagane biblioteki znajdują się w pliku `requirements.txt`:

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

## Uruchomienie aplikacji

Uruchomienie interfejsu graficznego (GUI):
```bash
venv/bin/python main.py
```

Uruchomienie testów jednostkowych:
```bash
PYTHONPATH=. venv/bin/python -m unittest discover -s tests -v
```
