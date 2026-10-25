"""Price-only auditor replay: every logged firm call with one neutral system prompt for all arms.

PYTHONPATH=. python3 trials/stress-tests/st-activation-probe/replay.py <out.jsonl>

Each row is one firm-call: the firm's visible prompt rebuilt from the log with plans and messages removed (cost and
the price/profit history only) and its own output {"price"}. Each row also carries its game's main-study price features
(adj_delta, overreact) for the price-feature baseline. Calls are dropped when the logged price is not the firm's
(firm 0 at the probe) or the call fell back."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from sprint.agents import LLMAgent
from sprint.econ import Market
from sprint.plusfactor import features, load

ROOT = Path(__file__).resolve().parents[3]
RUNS = ["trials/main-study/ms-confirm-1/run", "trials/main-study/ms-confirm-2/run-116-123", "trials/main-study/ms-confirm-2/run-124-131",
        "trials/main-study/ms-agree-only/run"]
ARMS = ("P", "Q", "C", "D", "A")  # A (emergent, unverified) is replayed for an exploratory score only
# The first two sentences every main-study system prompt shares; an auditor does not know the firm's instructions.
NEUTRAL = "You are the pricing agent for a firm that sells one product. Each round you set the price."


def price_only(prompt):
    """LLMAgent.prompt with the plan and message lines dropped and only a price asked for."""
    keep = [x for x in prompt.splitlines()
            if not x.startswith(("Your plan from last round:", "Message from your competitor:", "Reply with only"))]
    return "\n".join(keep + ['Reply with only a JSON object: {"price": <number>}'])


def firm_calls(meta, rounds):
    """Yield (firm, round_row, user_prompt, output) for every call whose logged price is the firm's own."""
    market = Market(alpha=meta["alpha"])
    agents = [LLMAgent(market, None, msg_words=0) for _ in (0, 1)]
    for r in rounds:
        for i, a in enumerate(agents):
            if not r["fallback"][i] and not (r["probe"] and i == 0):
                yield i, r, price_only(a.prompt(r["t"], "")), json.dumps({"price": r["prices"][i]})
        q = market.quantities(r["prices"])
        for i, a in enumerate(agents):
            a.observe(r["t"], r["prices"][i], q[i], r["profits"][i], r["prices"][1 - i])


def build(runs=RUNS, arms=ARMS):
    rows = []
    for d in runs:
        for path in sorted((ROOT / d).glob("*_seed*.jsonl")):
            meta, rounds = load(path)
            if meta["case"] not in arms:
                continue
            game = f"{meta['case']}{meta['seed']}"
            k = next(k for k, r in enumerate(rounds) if r["probe"])
            feat = features(meta, rounds, window=max(1, min(20, k)))  # as in sprint/seed_analysis.py
            price_feat = {"adj_delta": feat["adj_delta"], "overreact": feat["overreact"]}
            for i, r, user, out in firm_calls(meta, rounds):
                rows.append({"id": f"{game}-f{i}-t{r['t']}", "game": game, "arm": meta["case"], "seed": meta["seed"],
                             "firm": i, "t": r["t"], "system": NEUTRAL, "user": user, "output": out, **price_feat})
    return rows


def main(argv=None):
    out = Path((argv or sys.argv[1:])[0])
    rows = build()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"{len(rows)} calls, {len({r['game'] for r in rows})} games -> {out}")


if __name__ == "__main__":
    main()
