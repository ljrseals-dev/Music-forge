# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
"""Small Markov toolkit used by the modular generator.

- MarkovChain: variable-order (back-off) chain with add-alpha smoothing,
  temperature scaling and constraint injection (an `allowed` state set).
- entropy / repetition / diversity: diagnostics for judging generated lines.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict


class MarkovChain:
    def __init__(self, order: int = 2, alpha: float = 0.1):
        self.order = order
        self.alpha = alpha
        # tables[k] maps a context of length k to a Counter of successors
        self.tables = [defaultdict(Counter) for _ in range(order + 1)]

    def train(self, seq):
        for k in range(self.order + 1):
            for i in range(len(seq) - k):
                self.tables[k][tuple(seq[i:i + k])][seq[i + k]] += 1

    def sample(self, history, rng, temperature=1.0, allowed=None):
        """Sample the next state.

        Uses the longest context with training data (back-off), smooths with
        add-alpha so unseen transitions are unlikely but possible, restricts to
        `allowed` when given (constraint injection), then applies temperature.
        """
        counter = Counter()
        for k in range(min(self.order, len(history)), -1, -1):
            ctx = tuple(history[len(history) - k:]) if k else ()
            c = self.tables[k].get(ctx)
            if c:
                counter = c
                break
        support = sorted(allowed) if allowed is not None else sorted(counter)
        if not support:
            raise ValueError("MarkovChain has no states: train() it first")
        inv_t = 1.0 / max(temperature, 1e-3)
        weights = [(counter.get(s, 0) + self.alpha) ** inv_t for s in support]
        r = rng.random() * sum(weights)
        cum = 0.0
        for s, w in zip(support, weights):
            cum += w
            if r <= cum:
                return s
        return support[-1]


def conditional_entropy(seq):
    """H(X_t | X_{t-1}) in bits; low = predictable, high = surprising."""
    if len(seq) < 2:
        return 0.0
    pair = Counter(zip(seq, seq[1:]))
    prev = Counter(seq[:-1])
    n = len(seq) - 1
    return -sum((c / n) * math.log2(c / prev[a]) for (a, _b), c in pair.items())


def repetition(seq):
    """Share of consecutive pairs that are repeats of an earlier pair."""
    pairs = list(zip(seq, seq[1:]))
    return 0.0 if not pairs else 1.0 - len(set(pairs)) / len(pairs)


def diversity(seq):
    return len(set(seq))
