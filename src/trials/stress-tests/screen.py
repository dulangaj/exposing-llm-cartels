# Stress-test screen readout: per cell, price_overreact flags per arm, mean adj price Δ and fallbacks.
# python3 trials/stress-tests/screen.py <screen dir> <cell>... ; the first cell is the baseline the others are tested against.
import json, statistics, sys
from pathlib import Path
sys.path.insert(0, ".")
from sprint.seed_analysis import fisher_exact
ARMS, SIDE = "PQCD", {"P": "less", "Q": "greater", "C": "greater", "D": "greater"}  # SIDE: direction of the bar
root, cells = Path(sys.argv[1]), sys.argv[2:]


def cell(name):
    d, arms = root / name, {}
    runs = [r for r in json.loads((d / "rows.json").read_text())["runs"] if r["view"] == "both"]
    for r in runs:
        arms.setdefault(r["scenario"], []).append(r)
    fb = {s: sum(f for p in d.glob(f"{s}_seed*.jsonl") for l in p.read_text().splitlines()
                 for f in json.loads(l).get("fallback", [])) for s in ARMS}
    n = {s: len(list(d.glob(f"{s}_seed*.jsonl"))) for s in ARMS}
    return {s: {"k": sum(r["flags"]["price_overreact"] for r in xs), "n": len(xs), "games": n[s], "fb": fb[s],
                "delta": statistics.mean(r["adj_delta"] for r in xs)} for s, xs in arms.items()}


base = cell(cells[0])
print("| cell | P flags | Q flags | C flags | D flags | mean price Δ (P/Q/C/D) | fallbacks (P/Q/C/D) |")
print("|---|---|---|---|---|---|---|")
res = {c: cell(c) for c in cells}
for c, r in res.items():
    f = lambda s, k: r[s][k] if s in r else "-"
    print(f"| {c} | " + " | ".join(f"{r[s]['k']}/{r[s]['n']}" if s in r else "-" for s in ARMS)
          + " | " + "/".join(f"{r[s]['delta']:.2f}" if s in r else "-" for s in ARMS)
          + " | " + "/".join(str(f(s, "fb")) for s in ARMS) + " |")
print()
for c, r in list(res.items())[1:]:
    hits = []
    for s in (s for s in r if s in base):
        k, n, bk, bn = r[s]["k"], r[s]["n"], base[s]["k"], base[s]["n"]
        p = fisher_exact(k, n - k, bk, bn - bk, SIDE[s])
        dd = r[s]["delta"] - base[s]["delta"]
        crossed = (s == "P" and k < 6 / 8 * n) or (s != "P" and k >= 2 / 8 * n)
        if (s == "P" and bk < 6 / 8 * bn) or (s != "P" and bk >= 2 / 8 * bn):  # base already crosses: need a 2/8 move
            crossed = (k / n - bk / bn) * (-1 if s == "P" else 1) >= 2 / 8
        bar = crossed or abs(dd) >= 0.25
        hits.append(bar)
        print(f"{c} {s}: {k}/{n} vs {bk}/{bn}, one-sided ({SIDE[s]}) Fisher p = {p:.3g}; price Δ change {dd:+.2f}"
              + ("  NOTICEABLE" if bar else ""))
    print(f"{c}: {'noticeable' if any(hits) else 'not noticeable'}")
