"""Calvano et al. (2020) logit demand with Fish et al. (2024) price scale alpha."""
from __future__ import annotations

import math
from dataclasses import dataclass

ALPHAS = (1.0, 3.2, 10.0)  # Fish et al. (2024) price scales


def _argmax(f, lo, hi, iters=200):
    """Ternary search for the maximiser of a quasi-concave f on [lo, hi]."""
    for _ in range(iters):
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        if f(m1) < f(m2):
            lo = m1
        else:
            hi = m2
    return (lo + hi) / 2


@dataclass(frozen=True)
class Market:
    alpha: float = 1.0  # price scale: prices and costs are multiplied by alpha
    beta: float = 100.0  # quantity scale
    a: float = 2.0
    a0: float = 0.0
    mu: float = 0.25
    c: float = 1.0
    n: int = 2

    @property
    def cost(self):
        return self.alpha * self.c

    def quantities(self, prices):
        u = [(self.a - p / self.alpha) / self.mu for p in prices]
        u0 = self.a0 / self.mu
        top = max(u + [u0])
        e = [math.exp(x - top) for x in u]
        denom = sum(e) + math.exp(u0 - top)
        return [self.beta * x / denom for x in e]

    def profits(self, prices):
        return [(p - self.cost) * q for p, q in zip(prices, self.quantities(prices))]

    def best_response(self, i, prices):
        def own(p):
            trial = list(prices)
            trial[i] = p
            return self.profits(trial)[i]
        return _argmax(own, self.cost, self.cost + 10 * self.alpha)

    def nash_price(self):
        p = [self.cost] * self.n
        for _ in range(500):
            new = [self.best_response(i, p) for i in range(self.n)]
            if max(abs(x - y) for x, y in zip(new, p)) < 1e-10:
                break
            p = new
        return sum(p) / self.n

    def monopoly_price(self):
        return _argmax(lambda p: sum(self.profits([p] * self.n)), self.cost, self.cost + 10 * self.alpha)

    def benchmarks(self):
        pn, pm = self.nash_price(), self.monopoly_price()
        return {"p_nash": pn, "p_mon": pm,
                "pi_nash": self.profits([pn] * self.n)[0], "pi_mon": self.profits([pm] * self.n)[0]}


def collusion_index(profit, pi_nash, pi_mon):
    """Delta = (pi - pi_Nash) / (pi_Mon - pi_Nash): 0 at Nash, 1 at joint monopoly."""
    return (profit - pi_nash) / (pi_mon - pi_nash)
