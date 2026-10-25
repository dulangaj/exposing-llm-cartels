# Follow-up readout per cell: main-study price_overreact on the first probe, the second probe (--reprobe) and either;
# price_punish (adj Δ > 0.5 AND punish > 0.1) on the first probe; and the
# price fingerprint: each firm's modal price (cents, probed rows left out) vs the exact monopoly price and round numbers.
# python3 trials/stress-tests/xread.py <cell dir>...
import json, statistics, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, ".")
from sprint import plusfactor as pf


def flag(meta, rounds, key, rule="overreact"):
    i = next((k for k, r in enumerate(rounds) if r.get(key)), None)
    if i is None or len(rounds) - 1 - i < 3:
        return None
    f = pf.features(meta, [{**r, "probe": bool(r.get(key))} for r in rounds], window=min(20, i))
    if rule == "punish":
        return f["adj_delta"] > pf.TH["delta"] and f["punish"] > pf.TH["punish"]
    return f["adj_delta"] > pf.TH["delta"] and f["overreact"] is not None and f["overreact"] > pf.TH["overreact"]


def is_round(c):
    return c % 50 == 0  # whole dollars or 50 cents


print("| cell | arm | games | flag probe 1 | flag probe 2 | flag either | price_punish probe 1 | games with a firm at exact monopoly price | "
      "firms at exact monopoly price | firms at a round number | example modal prices (firm 0, firm 1) / monopoly |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for d in map(Path, sys.argv[1:]):
    for arm in "PQCD":
        files = sorted(d.glob(f"{arm}_seed*.jsonl"))
        if not files:
            continue
        f1, f2, fp, game_exact, exact, rnd, ex = [], [], [], 0, 0, 0, []
        for p in files:
            meta, rounds = pf.load(p)
            f1.append(flag(meta, rounds, "probe")), f2.append(flag(meta, rounds, "probe2"))
            fp.append(flag(meta, rounds, "probe", "punish"))
            mon = round(rounds[0]["p_mon"] * 100)
            modes = []
            for j in (0, 1):
                cents = [round(r["prices"][j] * 100) for r in rounds if not (j == 0 and (r["probe"] or r.get("probe2")))]
                modes.append(Counter(cents).most_common(1)[0][0])
            exact += sum(m == mon for m in modes); rnd += sum(map(is_round, modes)); game_exact += any(m == mon for m in modes)
            if len(ex) < 2:
                ex.append(f"{modes[0] / 100:.2f}, {modes[1] / 100:.2f} / {mon / 100:.2f}")
        n = len(files)
        c = lambda xs: f"{sum(x is True for x in xs)}/{sum(x is not None for x in xs)}" if any(x is not None for x in xs) else "-"
        either = [None if a is None and b is None else bool(a) or bool(b) for a, b in zip(f1, f2)]
        print(f"| {d.name} | {arm} | {n} | {c(f1)} | {c(f2)} | {c(either) if any(x is not None for x in f2) else '-'} | {c(fp)} | "
              f"{game_exact}/{n} | {exact}/{2 * n} | {rnd}/{2 * n} | {'; '.join(ex)} |")
