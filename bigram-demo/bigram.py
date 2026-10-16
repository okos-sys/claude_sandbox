"""A tiny "language model": count which word follows which, then sample.

Run:  uv run bigram.py
      uv run bigram.py --start i --temperature 0.5 --samples 5
"""

import argparse
import random
from collections import defaultdict

CORPUS = [
    "i think we should probably ship it",
    "i think we should probably wait",
    "i think we should check with the team",
    "i think that sounds good",
    "that sounds good to me",
]

END = "<end>"


def build_frequency_table(sentences):
    table = defaultdict(lambda: defaultdict(int))
    for sentence in sentences:
        words = sentence.split() + [END]
        for current, following in zip(words, words[1:]):
            table[current][following] += 1
    return table


def to_probabilities(row):
    total = sum(row.values())
    return {word: count / total for word, count in row.items()}


def apply_temperature(probabilities, temperature):
    if temperature == 0:
        best = max(probabilities, key=probabilities.get)
        return {word: (1.0 if word == best else 0.0) for word in probabilities}
    weights = {w: p ** (1 / temperature) for w, p in probabilities.items()}
    total = sum(weights.values())
    return {w: v / total for w, v in weights.items()}


def sample_next(row, temperature):
    probabilities = apply_temperature(to_probabilities(row), temperature)
    words = list(probabilities)
    return random.choices(words, weights=[probabilities[w] for w in words])[0]


def generate(table, start, temperature, max_words=12):
    words = [start]
    while len(words) < max_words and words[-1] in table:
        following = sample_next(table[words[-1]], temperature)
        if following == END:
            break
        words.append(following)
    return " ".join(words)


def print_table(table):
    print("FREQUENCY TABLE (row = current word, counts of the next word)")
    for word, row in table.items():
        cells = ", ".join(f"{w}: {c}" for w, c in row.items())
        print(f"  {word:>9} -> {cells}")


def print_probabilities(table):
    print("\nPROBABILITIES (each row normalized to 100%)")
    for word, row in table.items():
        cells = ", ".join(f"{w}: {p:.0%}" for w, p in to_probabilities(row).items())
        print(f"  {word:>9} -> {cells}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="i")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=5)
    args = parser.parse_args()

    table = build_frequency_table(CORPUS)
    print_table(table)
    print_probabilities(table)

    print(f"\nSAMPLING (start='{args.start}', temperature={args.temperature})")
    for _ in range(args.samples):
        print("  " + generate(table, args.start, args.temperature))


if __name__ == "__main__":
    main()
